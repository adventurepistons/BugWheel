import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pii_detection import detect_pii

def test_basic_regex_detection():
    text = "Contact Nikhil at nikhil@example.com or call +1-555-123-4567."
    results = detect_pii(text)
    for entity in results:
        print(entity)
    assert any(e.type == "EMAIL" for e in results)
    assert any(e.type == "PHONE" for e in results)

if __name__ == "__main__":
    test_basic_regex_detection()
    print("Test passed.") 