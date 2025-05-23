from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from typing import Tuple, Dict
import copy
import re
import logging
from cryptography.fernet import Fernet
import os

# Lowered confidence threshold for masking
PII_CONFIDENCE_THRESHOLD = 0.5

# List of attributes to check for PII (always skip 'value' for user-editable elements)
PII_ATTRS = ["id", "name", "aria_label", "placeholder", "title", "text_content"]

# Regex patterns for real PII
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_REGEX = re.compile(r"^(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4,}$")
SSN_REGEX = re.compile(r"^\d{3}-\d{2}-\d{4}$")
CREDIT_CARD_REGEX = re.compile(r"^(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})$")
# Add more patterns as needed

# Common PII types NOT covered by standard libraries or NLP (for future extensibility):
# - India Aadhar Number: 12 digits, e.g., 123412341234 (regex: ^\d{12}$)
# - India PAN: 5 letters, 4 digits, 1 letter, e.g., ABCDE1234F (regex: ^[A-Z]{5}[0-9]{4}[A-Z]$)
# - UK NINO (National Insurance Number): 2 letters, 6 digits, 1 letter, e.g., QQ123456C (regex: ^[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]$)
# - EU VAT numbers (various formats)
# - US Passport, Driver's License (various state formats)
# - Canada SIN: 9 digits, e.g., 123456789 (regex: ^\d{9}$)
# - Australia TFN: 8 or 9 digits (regex: ^\d{8,9}$)
# - Brazil CPF: 11 digits, e.g., 123.456.789-09 (regex: ^\d{3}\.\d{3}\.\d{3}-\d{2}$ or ^\d{11}$)
# - ... (add as needed for your use case)

def is_real_email(value):
    return EMAIL_REGEX.match(value.strip()) is not None

def is_real_phone(value):
    return PHONE_REGEX.match(value.strip()) is not None

def is_real_ssn(value):
    return SSN_REGEX.match(value.strip()) is not None

def is_real_credit_card(value):
    digits = re.sub(r'[\s-]', '', value.strip())
    return CREDIT_CARD_REGEX.match(digits) is not None

def is_probably_not_pii(value, attr):
    value = value.strip()
    # Skip all-uppercase short strings (likely country codes)
    if value.isupper() and len(value) <= 3:
        return True
    # Skip numeric values (likely prices)
    try:
        float(value)
        return True
    except ValueError:
        pass
    # Skip if value matches attribute name (case-insensitive)
    if value.lower() == attr.lower():
        return True
    # Skip if value is a single word, capitalized, and not a typical name
    if value.istitle() and ' ' not in value and len(value) < 20:
        return True
    # Skip if value is a single CamelCase or PascalCase word (common for field labels)
    if re.match(r'^[A-Z][a-z]+(?:[A-Z][a-z]+)+$', value):
        return True
    return False

# Print all loaded Presidio recognizers and their supported entity types
_printed_entity_types = False
def print_presidio_entity_types(analyzer: AnalyzerEngine):
    global _printed_entity_types
    if _printed_entity_types:
        return
    recognizers = analyzer.get_recognizers(language='en')
    all_entities = set()
    for rec in recognizers:
        all_entities.update(rec.supported_entities)
    logging.info(f"[PII ENTITY TYPES] Loaded Presidio entity types: {sorted(all_entities)}")
    _printed_entity_types = True

# Helper for context-aware fake value generation, always using attribute context
def get_contextual_fake_value(entity_type, original_value, fake: Faker, attr: str, el: dict):
    # Only generate a fake if the value matches a real PII pattern or is a high-confidence NLP entity
    if entity_type == "EMAIL_ADDRESS" and is_real_email(original_value):
        return fake.email()
    if entity_type == "PHONE_NUMBER" and is_real_phone(original_value):
        return fake.phone_number()
    if entity_type == "US_SSN" and is_real_ssn(original_value):
        return fake.ssn()
    if entity_type == "CREDIT_CARD" and is_real_credit_card(original_value):
        return fake.credit_card_number()
    # NLP-based types (names, orgs, locations, dates)
    if entity_type == "PERSON":
        return fake.name()
    if entity_type == "ORGANIZATION":
        return fake.company()
    if entity_type == "LOCATION":
        return fake.address()
    if entity_type == "DATE_TIME":
        return str(fake.date_of_birth())
    # Fallback: if not a real PII value, return the original value (do not mask)
    return original_value

def should_mask(entity_type, value, score, attr):
    value = value.strip()
    # Pattern-based types
    if entity_type == "EMAIL_ADDRESS":
        return is_real_email(value)
    if entity_type == "PHONE_NUMBER":
        return is_real_phone(value)
    if entity_type == "US_SSN":
        return is_real_ssn(value)
    if entity_type == "CREDIT_CARD":
        return is_real_credit_card(value)
    # NLP-based types (names, orgs, locations, dates)
    if entity_type in {"PERSON", "ORGANIZATION", "LOCATION", "DATE_TIME"}:
        if is_probably_not_pii(value, attr):
            return False
        return score > PII_CONFIDENCE_THRESHOLD
    # Add more entity-specific checks as needed
    return False  # Default: do not mask unless strict pattern matches or high-confidence NLP

def mask_pii_in_element(el: dict, analyzer: AnalyzerEngine, anonymizer: AnonymizerEngine, fake: Faker) -> Tuple[dict, Dict[str, str]]:
    print_presidio_entity_types(analyzer)
    el = copy.deepcopy(el)
    mapping = {}
    has_pii = False
    fake_values = []
    for attr in PII_ATTRS:
        if attr in el and el[attr]:
            text = el[attr]
            results = analyzer.analyze(text=text, language='en')
            # Debug logging for every value checked
            logging.info(f"[PII DEBUG] Checking attr '{attr}' with value '{text}':")
            for r in results:
                logging.info(f"  - Entity: {r.entity_type}, Score: {r.score}, Text: '{text[r.start:r.end]}'")
            filtered_results = [r for r in results if should_mask(r.entity_type, text[r.start:r.end], r.score, attr)]
            if filtered_results:
                has_pii = True
                operators = {}
                for r in filtered_results:
                    original_value = text[r.start:r.end]
                    fake_value = get_contextual_fake_value(r.entity_type, original_value, fake, attr, el)
                    operators[r.entity_type] = OperatorConfig("replace", {"new_value": fake_value})
                    mapping[original_value] = fake_value
                    fake_values.append(fake_value)
                anonymized = anonymizer.anonymize(text=text, analyzer_results=filtered_results, operators=operators)
                el[attr] = anonymized.text
    el["has_pii"] = has_pii
    el["fake_values"] = fake_values
    return el, mapping

PII_KEY_FILE = "pii_mapping.key"

# --- Encryption/Decryption Utilities ---
def get_or_create_encryption_key():
    if os.path.exists(PII_KEY_FILE):
        with open(PII_KEY_FILE, "rb") as f:
            return f.read()
    key = Fernet.generate_key()
    with open(PII_KEY_FILE, "wb") as f:
        f.write(key)
    return key

def encrypt_mapping_file(mapping: dict, target_file: str):
    import json
    key = get_or_create_encryption_key()
    fernet = Fernet(key)
    data = json.dumps(mapping, ensure_ascii=False, indent=2).encode()
    encrypted = fernet.encrypt(data)
    with open(target_file, "wb") as f:
        f.write(encrypted)

def decrypt_mapping_file(target_file: str) -> dict:
    import json
    key = get_or_create_encryption_key()
    fernet = Fernet(key)
    with open(target_file, "rb") as f:
        encrypted = f.read()
    data = fernet.decrypt(encrypted)
    return json.loads(data.decode()) 