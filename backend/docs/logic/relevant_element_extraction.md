# Extracting Relevant UI Elements for LLM Test Generation

## Introduction
Selecting the right subset of UI elements from a large ApplicationModel is crucial for generating high-quality, actionable test steps with an LLM. This document outlines three strategies, from simple to advanced, for extracting relevant elements to include in your LLM prompt. Start with Keyword Matching for your MVP, and evolve to more advanced methods as needed.

---

## Strategy 1: Keyword Matching (Recommended for MVP)
**Description:**
- Extract keywords from the user's requirements text.
- Match these keywords against element descriptions, types, and attributes in your ApplicationModel.
- Build a concise list of relevant elements for the LLM prompt.

**Sample Code:**
```python
import re

def extract_keywords(text):
    stop_words = set(["a", "an", "the", "to", "be", "is", "of", "and", "in", "with", "my", "i", "want", "as", "user", "able", "for", "on", "button", "field"])
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    keywords = [word for word in text.split() if word not in stop_words and len(word) > 2]
    if "log in" in text or "login" in text:
        keywords.extend(["login", "sign in", "username", "password", "submit", "account"])
    return list(set(keywords))

def get_relevant_elements(requirements_text, application_model, max_elements=20):
    keywords = extract_keywords(requirements_text)
    relevant_elements = []
    seen_element_ids = set()
    for page in application_model.get("pages", []):
        page_url = page.get("url")
        page_title = page.get("title")
        page_keywords = extract_keywords(f"{page_title} {page_url}")
        if any(kw in page_keywords for kw in keywords):
            relevant_elements.append({
                "type": "page",
                "description": f"Page: {page_title} ({page_url})",
                "url": page_url
            })
        for element in page.get("elements", []):
            if len(relevant_elements) >= max_elements:
                break
            element_desc = element.get("description", "").lower()
            element_type = element.get("type", "").lower()
            element_id = element.get("unique_id")
            if element_id in seen_element_ids:
                continue
            is_relevant = False
            for keyword in keywords:
                if keyword in element_desc or keyword in element_type:
                    is_relevant = True
                    break
                for locator in element.get("locators", []):
                    if keyword in str(locator.get("value", "")).lower():
                        is_relevant = True
                        break
                if is_relevant:
                    break
            if is_relevant:
                relevant_elements.append({
                    "description": element.get("description"),
                    "type": element.get("type"),
                    "id": next((loc["value"] for loc in element.get("locators", []) if loc["type"] == "id"), None),
                    "url_on_page": page_url
                })
                seen_element_ids.add(element_id)
    return relevant_elements[:max_elements]
```

**Tips:**
- Weight elements by number of keyword matches.
- Limit to the most relevant pages/elements.
- Prioritize semantic attributes (e.g., `data-test-id`, `aria-label`).

---

## Strategy 2: Semantic Search (Future Enhancement)
**Description:**
- Use embeddings to represent requirements and element descriptions.
- Compute similarity and select top-K most relevant elements.
- Requires embedding API (e.g., OpenAI, Cohere) and vector search.

**Logic:**
- Precompute embeddings for ApplicationModel elements.
- Embed requirements_text at runtime.
- Use cosine similarity to find best matches.

**When to Use:**
- When you need better relevance, synonym support, or have a large model.

---

## Strategy 3: Heuristic-Based Filtering (Can Combine with Others)
**Description:**
- Apply rules based on element type, interactivity, and page locality.
- E.g., prioritize input fields for "enter" actions, buttons for "click" actions, etc.

**Logic:**
- Filter by type (input, button, etc.)
- Filter by interactivity
- Filter by page context (e.g., "login page")

---

## LLM Prompt Construction Example
Once you have your relevant elements, embed them in the LLM prompt:

```python
prompt = f"""
## User Requirement:
{requirements_text}

## Application UI Model (Relevant Pages/Elements):
Below are UI elements from the application that are potentially relevant to the user's requirement.
Focus on using the 'description' field for 'element_description' in your test steps.
If an element is not explicitly listed but logically implied, use a general but precise description (e.g., 'any input field', 'navigation bar', 'main content area').
If a step requires navigating to a specific URL, ensure the 'action' is 'Navigate' and 'element_description' is the page name/type, and 'value' is the URL.

```json
{json.dumps(relevant_elements_json, indent=2)}
```
Allowed Actions and Expected Output Format (JSON Array of Objects):
Each step must be clear, actionable, and include an 'element_description' that maps directly to an element from the model OR a general description.
Provide a 'value' if an input/selection action is required. Provide a clear 'expected_result'.

Allowed 'action' types:
- Navigate
- Type
- Click
- Check
- Select
- AssertText
- AssertElementPresent
- WaitForElement

[...see full prompt in project docs...]
"""
```

---

## How to Use
- Start with **Keyword Matching** for your MVP.
- As your ApplicationModel grows, consider **Semantic Search** for better accuracy.
- Combine with **Heuristic Filtering** for domain-specific rules.
- Update this doc as your extraction logic evolves!

---

## Privacy-First Workflow for PII Masking and Test Automation

The following diagram illustrates the privacy-first workflow for extracting, masking, and processing UI elements for LLM-driven test automation. This approach ensures 100% masking of all PII on the user's machine, with only placeholder-masked data ever leaving the local environment. The real value-to-placeholder mapping is securely stored locally, enabling remapping for test execution without exposing PII to the cloud or LLM.

```mermaid
graph TD
    A[Scan UI Elements on User Machine] --> B{Detect PII in Elements}
    B -->|PII Found| C[Replace PII with Deterministic Placeholders (e.g., EMAIL_1)]
    C --> D[Store Mapping (PII <-> Placeholder) Locally (Encrypted)]
    C --> E[Build Masked Application Map]
    E --> F[Store Masked Map in Cloud Backend (Optional)]
    E --> G[Send Masked Elements/Descriptions to LLM]
    G --> H[LLM Returns Test Step Mappings (Placeholders Only)]
    H --> I[Generate Playwright/Test Script (Placeholders Only)]
    I --> J[Remap Placeholders to Real Values Locally]
    J --> K[Execute Test Locally with Real Data]
```

**Key Points:**
- All PII detection and masking occurs locally.
- Only masked data (with placeholders) is sent to the cloud or LLM.
- The mapping between real values and placeholders is never exposed outside the user's machine.
- Test execution with real data happens locally after remapping.

This workflow enables secure, privacy-first test automation and is fully compatible with cloud storage and LLM-driven test generation, without any risk of PII exposure. 