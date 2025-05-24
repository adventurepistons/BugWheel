from typing import List
from .types import PIIEntity

def presidio_pii_detector(text: str, analyzer=None) -> List[PIIEntity]:
    if analyzer is None:
        from presidio_analyzer import AnalyzerEngine
        analyzer = AnalyzerEngine()
    results = analyzer.analyze(text=text, language="en")
    pii_entities = []
    for res in results:
        pii_entities.append(
            PIIEntity(
                type=res.entity_type,
                value=text[res.start:res.end],
                start=res.start,
                end=res.end,
                confidence=res.score,
                detector="presidio"
            )
        )
    return pii_entities 