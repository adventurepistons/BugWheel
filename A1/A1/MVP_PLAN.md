# MVP Plan: Privacy-First, User-Driven LLM Test Automation

## 1. User Input (Web App)
- User enters:
  - The URL of the web application to test.
  - Test steps in a custom DSL (Domain-Specific Language).
- UI/UX:
  - Simple form for URL and test steps.
  - DSL editor with syntax highlighting (optional for MVP).

## 2. Local Agent: DOM Scanning & Locator Extraction
- Trigger:
  - When the user clicks "Execute" or "Create", the web app sends the URL and test steps to the local agent.
- Local agent actions:
  - Launches browser, navigates to the URL.
  - Scans the DOM, finds all relevant elements.
  - For each element, finds the best locator (CSS/XPath/ARIA, etc.).
  - Groups elements by page (if multi-page flow).
  - Generates a unique, human-readable description for each element (excluding value attributes and obvious PII).
  - Merges duplicate elements (across pages or within a page) to avoid redundancy.

## 3. Application Map Transfer & User Review
- The local agent sends the merged application map (with element locators and generated descriptions) to the web app.
- Web app UI:
  - Shows a paginated or tabbed list of all pages and their elements.
  - For each element, displays the generated description in an editable text box.
  - User can review and edit any description to remove/clean PII or improve clarity.
  - Optionally, highlight or flag fields that may contain PII (e.g., if the description contains suspicious patterns).

## 4. Saving the Application Map
- Once the user is satisfied:
  - User clicks "Save" or "Finalize".
  - The cleaned, user-reviewed application map is saved in the web app's backend (or local storage, depending on architecture).
  - Optionally, allow the user to re-edit or re-scan as needed.

## 5. LLM Mapping for Test Step Execution
- When ready to generate test code:
  - The web app sends the finalized element descriptions and the user's test steps to the LLM.
  - Only the descriptions and test steps are sent to the LLM—never raw DOM, values, or other potentially sensitive data.
  - The LLM maps test steps to elements using the descriptions, and generates the required test code or actions.

## 6. Execution & Feedback
- Generated test code is sent back to the local agent for execution (if desired).
- Results are displayed to the user.
- User can iterate:
  - Edit descriptions, re-run mapping, or adjust test steps as needed.

## 7. Privacy & PII Handling
- No automated PII detection/masking for MVP.
- User is responsible for reviewing and cleaning descriptions before anything is sent to the LLM.
- Value attributes and other likely PII sources are excluded from descriptions by default.
- All DOM scanning and locator extraction happens locally.
- Only user-reviewed, cleaned descriptions are sent to the LLM.
- (Optional for MVP) Add a warning or checklist for users to double-check for PII before finalizing.

## 8. Future Enhancements (Post-MVP)
- Add automated PII detection/masking as a helper (not a blocker).
- Add user feedback loop for improving description quality and PII detection.
- Support for authenticated flows and more complex test scenarios.
- More advanced merging/deduplication logic for elements.
- UI/UX polish, DSL improvements, and LLM prompt tuning.

---

## Summary Table

| Step | Action | Privacy/PII Handling |
|------|--------|----------------------|
| 1    | User enters URL & test steps | No PII risk |
| 2    | Local agent scans DOM, finds locators, generates descriptions | Value attributes excluded, all local |
| 3    | User reviews/edits descriptions in web UI | User manually removes PII |
| 4    | Save cleaned application map | Only cleaned data stored |
| 5    | Send descriptions + test steps to LLM | Only user-reviewed, non-PII data sent |
| 6    | Execute tests, show results | No PII risk |
| 7    | (Optional) Add warnings/checks for PII | User-driven, can add automation later |

</rewritten_file> 