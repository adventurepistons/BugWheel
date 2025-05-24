# Utility functions for PII detection (to be implemented as needed) 

import json
import os
from typing import Dict, List, Tuple
from .types import PIIEntity

# Path to the local placeholder list (update as needed)
PLACEHOLDER_LIST_PATH = os.path.join(os.path.dirname(__file__), 'placeholders.json')

# Cache for loaded placeholders
_PLACEHOLDER_CACHE = None

# Priority order for PII types (customize as needed)
PII_TYPE_PRIORITY = [
    'SSN', 'CREDIT_CARD', 'EMAIL', 'EMAIL_ADDRESS', 'PHONE', 'PERSON', 'NAME', 'ADDRESS', 'DATE', 'POSTAL_CODE', 'IP_ADDRESS', 'PASSPORT', 'NATIONAL_ID', 'BANK_ACCOUNT', 'USERNAME', 'MEDICAL_RECORD', 'URL'
]

def load_placeholder_list(path: str = PLACEHOLDER_LIST_PATH) -> Dict[str, dict]:
    global _PLACEHOLDER_CACHE
    if _PLACEHOLDER_CACHE is not None:
        return _PLACEHOLDER_CACHE
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    _PLACEHOLDER_CACHE = data.get('placeholders', {})
    return _PLACEHOLDER_CACHE

def get_placeholder(pii_type: str, index: int = 1) -> str:
    """
    Return a standardized placeholder string for a given PII type and index.
    E.g., get_placeholder('EMAIL', 2) -> 'EMAIL_2'
    """
    placeholders = load_placeholder_list()
    if pii_type not in placeholders:
        # Fallback to generic
        return f"{pii_type.upper()}_{index}"
    return f"{pii_type.upper()}_{index}"

def resolve_overlaps(entities: List[PIIEntity]) -> List[PIIEntity]:
    """
    Remove overlapping entities, keeping the one with highest priority/confidence/length.
    """
    # Sort by: start, -confidence, -length, type priority
    def entity_sort_key(e: PIIEntity):
        type_priority = PII_TYPE_PRIORITY.index(e.type.upper()) if e.type.upper() in PII_TYPE_PRIORITY else len(PII_TYPE_PRIORITY)
        return (e.start, -(e.confidence or 1.0), -(e.end - e.start), type_priority)
    sorted_entities = sorted(entities, key=entity_sort_key)
    result = []
    occupied = set()
    for e in sorted_entities:
        overlap = False
        for i in range(e.start, e.end):
            if i in occupied:
                overlap = True
                break
        if not overlap:
            result.append(e)
            for i in range(e.start, e.end):
                occupied.add(i)
    return result

def mask_and_map(text: str, pii_entities: List[PIIEntity]) -> Tuple[str, Dict[str, str]]:
    """
    Replace each detected PII value in text with a standardized placeholder.
    Returns (masked_text, mapping_dict)
    mapping_dict: {placeholder: real_value}
    """
    # Step 1: Resolve overlaps/conflicts
    filtered_entities = resolve_overlaps(pii_entities)
    # Step 2: Assign placeholders and mask
    sorted_entities = sorted(filtered_entities, key=lambda e: e.start, reverse=True)
    placeholder_counts = {}
    mapping = {}
    masked_text = text
    for entity in sorted_entities:
        key = entity.type.upper()
        # Assign index for each type
        if key not in placeholder_counts:
            placeholder_counts[key] = 1
        else:
            placeholder_counts[key] += 1
        placeholder = get_placeholder(key, placeholder_counts[key])
        # Replace in text
        masked_text = masked_text[:entity.start] + placeholder + masked_text[entity.end:]
        mapping[placeholder] = entity.value
    return masked_text, mapping 