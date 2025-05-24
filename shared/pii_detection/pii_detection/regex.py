import re
from .types import PIIEntity
from typing import List

def regex_pii_detector(text: str) -> List[PIIEntity]:
    patterns = {
        # Email
        "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        # Phone (international and US formats)
        "PHONE": r"\b(?:\+?\d{1,3}[\s-]?)?(?:\(\d{1,4}\)[\s-]?)?\d{1,4}[\s-]?\d{1,4}[\s-]?\d{1,9}\b",
        # US SSN
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        # Credit Card (simple, not Luhn validated)
        "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
        # Date (YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY)
        "DATE": r"\b(\d{4}[-/]\d{2}[-/]\d{2}|\d{2}[-/]\d{2}[-/]\d{4})\b",
        # Postal/ZIP code (US, 5 or 9 digits)
        "POSTAL_CODE": r"\b\d{5}(?:-\d{4})?\b",
        # IP Address (IPv4)
        "IP_ADDRESS": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        # Simple Name (capitalized words, 2+ words, not at start of sentence)
        # This is a naive pattern for demo purposes only
        "NAME": r"\b([A-Z][a-z]+\s[A-Z][a-z]+)\b"
    }
    results = []
    for pii_type, pattern in patterns.items():
        for match in re.finditer(pattern, text):
            results.append(
                PIIEntity(
                    type=pii_type,
                    value=match.group(),
                    start=match.start(),
                    end=match.end(),
                    confidence=1.0,
                    detector="regex"
                )
            )
    return results 