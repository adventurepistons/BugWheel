from dataclasses import dataclass
from typing import Optional

@dataclass
class PIIEntity:
    type: str  # e.g., EMAIL, NAME, SSN
    value: str  # The detected PII value
    start: int  # Start index in the text
    end: int    # End index in the text
    confidence: Optional[float] = None  # Confidence score (0-1), if available
    detector: Optional[str] = None      # Which detector found it (regex, spacy, etc.) 