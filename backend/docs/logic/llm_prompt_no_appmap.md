# LLM Prompt for Test Case Generation (No Application Map)

## Overview
For the MVP, you can generate functional test steps directly from user requirements without needing a full application model. This approach lets you validate your LLM integration and test step generation flow quickly. You can add application context later.

---

## Prompt Template
```
You are an expert QA engineer and test automation specialist. Your task is to generate precise, executable functional test steps based on user requirements for a generic web application. Each step must be clear, actionable, and include an 'element_description' that concisely identifies the UI element. Provide a 'value' if an input action is required. Provide a clear 'expected_result'.

The output MUST be a JSON array of test step objects, conforming to the exact schema provided. Do not include any additional text or explanations outside the JSON.

## User Requirement:
{requirements_text}

## Allowed Actions and Expected Output Format (JSON Array of Objects):
Each step must be clear, actionable, and include an 'element_description' that logically identifies the UI element. Provide a 'value' if an input/selection action is required. Provide a clear 'expected_result'.

Allowed 'action' types and their usage:
- Navigate: To go to a specific URL. Requires 'value' as the full URL.
- Type: To input text into a text field or text area. Requires 'value' as the text to be typed.
- Click: To click a button, link, checkbox, radio button, or any clickable element.
- Check: To check or uncheck a checkbox or radio button.
- Select: To select an option from a dropdown or select box. Requires 'value' as the exact visible text of the option to select.
- AssertText: To verify specific text is present on the page or within a particular element. Requires 'value' as the exact text to assert.
- AssertElementPresent: To verify a UI element is visible and interactive on the page.
- WaitForElement: To pause execution until a specific element appears on the page.

```json
[
  {
    "action": "(Navigate|Type|Click|Check|Select|AssertText|AssertElementPresent|WaitForElement)",
    "element_description": "<concise description of the UI element, e.g., 'Login button', 'Username input field', 'Dashboard page header', 'Terms and Conditions checkbox'>",
    "value": "<value to type/select, if applicable, or URL for Navigate>",
    "expected_result": "<clear and verifiable outcome of the step, what should be seen/happen>"
  }
]
```
Generate the test steps based on the user requirement, strictly following the exact JSON format and using only the allowed action types:
```

---

## How to Use
1. Replace `{requirements_text}` with the actual user input from the frontend.
2. Send the prompt to your LLM (e.g., OpenAI GPT-3.5/4) via API.
3. Parse the JSON array from the LLM's response.
4. Validate the output (fields, allowed actions, etc.).
5. Return the steps to the frontend.

---

## Why Start This Way?
- **Fastest path to value:** You can demo and test the core LLM-powered workflow immediately.
- **No dependency on application model:** Add UI context later as your product matures.
- **Easy to extend:** When ready, just augment the prompt with relevant UI elements. 