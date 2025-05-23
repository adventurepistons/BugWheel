import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from faker import Faker
from presidio_anonymizer.entities import OperatorConfig
import json

# Path to the test HTML file
HTML_PATH = str(Path(__file__).parent.parent / "test_pii.html")
HTML_URL = f"file:///{HTML_PATH.replace(os.sep, '/')}"

fake = Faker()

# Simple mapping for PII entity types to Faker methods
FAKER_MAP = {
    "PERSON": lambda: fake.name(),
    "EMAIL_ADDRESS": lambda: fake.email(),
    "PHONE_NUMBER": lambda: fake.phone_number(),
    "LOCATION": lambda: fake.address(),
    "CREDIT_CARD": lambda: fake.credit_card_number(),
    "US_SSN": lambda: fake.ssn(),
    "DATE_TIME": lambda: str(fake.date_of_birth()),
    "IBAN_CODE": lambda: fake.iban(),
    "IP_ADDRESS": lambda: fake.ipv4(),
    "PASSPORT": lambda: fake.passport_number(),
    "NRP": lambda: fake.ssn(),
    "ORGANIZATION": lambda: fake.company(),
    "USERNAME": lambda: fake.user_name(),
    "PASSWORD": lambda: fake.password(),
    "MEDICAL_LICENSE": lambda: "MRN" + fake.bothify(text="#######"),
}

def get_fake_value(entity_type, original_value):
    if entity_type in FAKER_MAP:
        return FAKER_MAP[entity_type]()
    else:
        return f"<PII:{entity_type}>"

async def extract_text_and_inputs(page):
    # Get all visible text
    body_text = await page.inner_text('body')
    # Get all input values
    input_values = await page.eval_on_selector_all('input', 'els => els.map(e => e.value)')
    # Get all password input values and their indices
    password_inputs = await page.eval_on_selector_all('input[type="password"]', 'els => els.map(e => e.value)')
    return body_text + "\n" + "\n".join(input_values), input_values, password_inputs

async def main():
    analyzer = AnalyzerEngine()
    anonymizer = AnonymizerEngine()
    pii_mapping = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        print(f"Opening {HTML_URL}")
        await page.goto(HTML_URL)
        text, input_values, password_inputs = await extract_text_and_inputs(page)
        print("\nExtracted text and input values:")
        print(text)
        # Mask password input values before PII detection
        for pw in password_inputs:
            if pw:
                fake_pw = get_fake_value("PASSWORD", pw)
                text = text.replace(pw, fake_pw)
                pii_mapping[pw] = fake_pw
        # Detect PII
        results = analyzer.analyze(text=text, language='en')
        print("\nDetected PII:")
        for r in results:
            print(f" - {r.entity_type}: {text[r.start:r.end]}")
        # Build anonymizer operators and mapping
        operators = {}
        for r in results:
            original_value = text[r.start:r.end]
            fake_value = get_fake_value(r.entity_type, original_value)
            operators[r.entity_type] = OperatorConfig("replace", {"new_value": fake_value})
            pii_mapping[original_value] = fake_value
        # Mask PII
        anonymized = anonymizer.anonymize(text=text, analyzer_results=results, operators=operators)
        print("\nMasked output:")
        print(anonymized.text)
        # Save masked output
        with open("masked_output.txt", "w", encoding="utf-8") as f:
            f.write(anonymized.text)
        print("\nMasked output saved to masked_output.txt")
        # Save mapping
        with open("pii_mapping.json", "w", encoding="utf-8") as f:
            json.dump(pii_mapping, f, indent=2, ensure_ascii=False)
        print("PII mapping saved to pii_mapping.json")
        # TODO: Encrypt the mapping file in production
        # TODO: Add user-supplied password support for encryption
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main()) 