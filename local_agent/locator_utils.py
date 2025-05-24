"""
Locator extraction, scoring, and uniqueness logic (ported from JS)
- Generate all possible locators for an element
- Generate all possible CSS selectors and XPaths
- Score and check uniqueness
- Select best locator, best unique CSS, best unique XPath

Best Locator Selection Logic:
1. Only consider unique locators with score >= threshold (default 70).
2. If none, fallback to unique relative XPath (if provided).
3. If none, fallback to unique relative CSS (if provided).
4. If none, return None.
Non-unique locators are never used as best locator for test case generation.
"""
from collections import defaultdict
import spacy

LOCATOR_SCORES = {
    'id': 100,
    'name_type': 95,
    'label': 90,
    'aria-label': 85,
    'role': 85,
    'class': 80,
    'data': 75,
    'name': 70,
    'placeholder': 60,
    'title': 60,
    'value': 60,
    'type': 60,
    'text': 50,
    'css': 25,
    'xpath': 30,
}

nlp = spacy.load("en_core_web_sm")

def is_unstable_class(cls):
    """Penalize classes that look auto-generated."""
    import re
    return bool(re.match(r'^(Mui|ant-|[A-Za-z0-9]{8,})', cls))

def generate_basic_locators(el):
    """Generate basic locators for an element (id, class, name, etc.)."""
    locators = []
    if el.get('id'):
        locators.append({'type': 'id', 'value': f"#{el['id']}"})
    if el.get('class'):
        classes = el['class'].split()
        if classes:
            locators.append({'type': 'class', 'value': '.' + '.'.join(classes)})
    if el.get('name'):
        locators.append({'type': 'name', 'value': f"[name='{el['name']}']"})
    if el.get('name') and el.get('type'):
        locators.append({'type': 'name_type', 'value': f"[name='{el['name']}'][type='{el['type']}']"})
    if el.get('aria_label'):
        locators.append({'type': 'aria-label', 'value': f"[aria-label='{el['aria_label']}']"})
    if el.get('role'):
        locators.append({'type': 'role', 'value': f"[role='{el['role']}']"})
    if el.get('attributes', {}).get('placeholder'):
        locators.append({'type': 'placeholder', 'value': f"[placeholder='{el['attributes']['placeholder']}']"})
    if el.get('attributes', {}).get('title'):
        locators.append({'type': 'title', 'value': f"[title='{el['attributes']['title']}']"})
    # Always skip 'value' locator for user-editable elements
    if el.get('value') and el.get('tag') not in ['input', 'textarea', 'select']:
        locators.append({'type': 'value', 'value': f"[value='{el['value']}']"})
    if el.get('type'):
        locators.append({'type': 'type', 'value': f"[type='{el['type']}']"})
    if el.get('text'):
        locators.append({'type': 'text', 'value': el['text']})
    # data-* attributes
    for k, v in el.get('attributes', {}).items():
        if k.startswith('data-'):
            locators.append({'type': 'data', 'value': f"[{k}='{v}']"})
    return locators

def is_unique(type_, value, elements):
    """Check if a locator is unique among all elements."""
    count = 0
    for e in elements:
        if type_ == 'id' and e.get('id') and f"#{e['id']}" == value:
            count += 1
        elif type_ == 'class' and e.get('class') and ('.' + '.'.join(e['class'].split())) == value:
            count += 1
        elif type_ == 'name' and e.get('name') and f"[name='{e['name']}']" == value:
            count += 1
        elif type_ == 'name_type' and e.get('name') and e.get('type') and f"[name='{e['name']}'][type='{e['type']}']" == value:
            count += 1
        elif type_ == 'aria-label' and e.get('aria_label') and f"[aria-label='{e['aria_label']}']" == value:
            count += 1
        elif type_ == 'role' and e.get('role') and f"[role='{e['role']}']" == value:
            count += 1
        elif type_ == 'placeholder' and e.get('attributes', {}).get('placeholder') and f"[placeholder='{e['attributes']['placeholder']}']" == value:
            count += 1
        elif type_ == 'title' and e.get('attributes', {}).get('title') and f"[title='{e['attributes']['title']}']" == value:
            count += 1
        elif type_ == 'value' and e.get('value') and f"[value='{e['value']}']" == value:
            count += 1
        elif type_ == 'type' and e.get('type') and f"[type='{e['type']}']" == value:
            count += 1
        elif type_ == 'text' and e.get('text') and e['text'] == value:
            count += 1
        elif type_ == 'data' and e.get('attributes'):
            for k, v in e['attributes'].items():
                if k.startswith('data-') and f"[{k}='{v}']" == value:
                    count += 1
    return count == 1

def score_locator(locator):
    """Score a locator based on type. Penalize unstable classes for class locators. Boost semantic attributes. Add dynamic scoring based on element context."""
    base_score = LOCATOR_SCORES.get(locator['type'], 10)
    # Penalize unstable classes
    if locator['type'] == 'class':
        cls = locator['value'].lstrip('.') if locator['value'].startswith('.') else locator['value']
        first_class = cls.split('.')[0]
        if is_unstable_class(first_class):
            return base_score - 30  # Penalize by 30
    # Boost semantic attributes
    if locator['type'] == 'data' or locator['type'] == 'aria-label':
        return base_score + 20  # Boost by 20 for semantic attributes
    # Dynamic scoring: prefer text for buttons/links, id/name for inputs
    element_tag = locator.get('element_tag')
    if locator['type'] == 'text' and element_tag in ['button', 'a']:
        return base_score + 20  # Prefer text for buttons/links
    if locator['type'] in ['id', 'name'] and element_tag in ['input', 'select', 'textarea']:
        return base_score + 15  # Prefer id/name for form fields
    return base_score

def select_best_locator(locators, best_unique_xpath=None, best_unique_css=None, threshold=70):
    """
    Select the best locator for test case generation.
    1. Only consider unique locators with score >= threshold.
    2. If none, fallback to unique relative XPath (if provided).
    3. If none, fallback to unique relative CSS (if provided).
    4. If none, return None.
    """
    unique_locators = [l for l in locators if l.get('unique') and score_locator(l) >= threshold]
    if unique_locators:
        return max(unique_locators, key=score_locator)
    if best_unique_xpath:
        return {'type': 'xpath', 'value': best_unique_xpath, 'unique': True, 'score': LOCATOR_SCORES['xpath']}
    if best_unique_css:
        return {'type': 'css', 'value': best_unique_css, 'unique': True, 'score': LOCATOR_SCORES['css']}
    return None

def generate_description(el):
    tag = el.get("tag", "")
    attrs = [
        el.get("aria_label", ""),
        el.get("attributes", {}).get("placeholder", ""),
        el.get("text_content", ""),
        el.get("text", ""),
        el.get("name", ""),
        el.get("id", "")
    ]
    # Combine all possible labels
    label = " ".join([a for a in attrs if a]).strip()
    doc = nlp(label)
    # Try to extract the most relevant entity
    for ent in doc.ents:
        if ent.label_ in {"PERSON", "ORG", "GPE", "PRODUCT"}:
            label = ent.text
            break
    # Fallback: use the most frequent noun
    if not label:
        nouns = [token.lemma_ for token in doc if token.pos_ == "NOUN"]
        if nouns:
            label = nouns[0]
    # Heuristic fallback if still no label
    if not label:
        label = el.get("name", "") or el.get("id", "")
    # Build description
    if tag == "button":
        return f"{label} button" if label else "Button"
    if tag == "input":
        label_str = label or ""
        if isinstance(label_str, str) and "password" in label_str.lower():
            return "Password input field"
        if isinstance(label_str, str) and "email" in label_str.lower():
            return "Email input field"
        if isinstance(label_str, str) and "user" in label_str.lower():
            return "Username input field"
        return f"{label} input field" if label else "Input field"
    if tag == "select":
        label_str = label or ""
        if isinstance(label_str, str) and "country" in label_str.lower():
            return "Country selection dropdown"
        return f"{label} dropdown" if label else "Dropdown"
    return f"{label} {tag}".strip() if label else tag.capitalize()

# TODO: Add functions to generate all possible CSS selectors and XPaths for an element (using attributes, parent context, nth-child, etc.)
# TODO: Add functions to check uniqueness of CSS/XPath selectors among all elements
# TODO: Integrate with Playwright element extraction for real DOM context 