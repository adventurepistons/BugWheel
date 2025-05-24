from typing import List
from .types import PIIEntity

# Use only Presidio for detection, with large model
from .presidio import presidio_pii_detector
from .regex import regex_pii_detector
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
import spacy

# Singleton analyzer instance
def get_large_presidio_analyzer():
    nlp_configuration = {
        "nlp_engine_name": "spacy",
        "models": [
            {"lang_code": "en", "model_name": "en_core_web_lg"}
        ]
    }
    provider = NlpEngineProvider(nlp_configuration=nlp_configuration)
    nlp_engine = provider.create_engine()
    return AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["en"])

_ANALYZER = get_large_presidio_analyzer()

# Singleton for spaCy NER (small model for speed)
_SPACY_NLP = None
def get_spacy_nlp():
    global _SPACY_NLP
    if _SPACY_NLP is None:
        _SPACY_NLP = spacy.load("en_core_web_sm")
    return _SPACY_NLP

def spacy_ner_pii_detector(text: str) -> List[PIIEntity]:
    nlp = get_spacy_nlp()
    doc = nlp(text)
    # Only include spaCy NER labels that are highly likely to be PII
    label_map = {
        "PERSON": "NAME",
        "GPE": "LOCATION",
        "LOC": "LOCATION",
        "DATE": "DATE",
        # Uncomment the next line if you want to treat organizations as PII
        # "ORG": "ORGANIZATION_NAME",
    }
    allowed_labels = set(label_map.keys())
    results = []
    for ent in doc.ents:
        if ent.label_ in allowed_labels:
            pii_type = label_map[ent.label_]
            results.append(
                PIIEntity(
                    type=pii_type,
                    value=ent.text,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=1.0,
                    detector="spacy_ner"
                )
            )
    return results

def detect_pii(text: str, analyzer=None) -> List[PIIEntity]:
    if analyzer is None:
        analyzer = _ANALYZER
    presidio_results = presidio_pii_detector(text, analyzer=analyzer)
    regex_results = regex_pii_detector(text)
    spacy_results = spacy_ner_pii_detector(text)
    # Ensemble: Only keep entities detected by at least two detectors (by type and value)
    all_results = presidio_results + regex_results + spacy_results
    # Count occurrences by (type, value)
    from collections import Counter, defaultdict
    entity_counter = Counter((e.type, e.value) for e in all_results)
    # Only keep entities found by at least two detectors
    seen = set()
    ensemble = []
    for e in all_results:
        key = (e.type, e.value)
        if entity_counter[key] >= 2 and key not in seen:
            ensemble.append(e)
            seen.add(key)
    return ensemble 