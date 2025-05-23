# Local Agent Roadmap & Architecture

## Overview
The Local Agent is a standalone application (installer) that runs on the user's machine. Its primary role is to scan the user's Application Under Test (AUT), extract a comprehensive application map, sanitize sensitive data, and communicate progress/results to the cloud backend for AI-driven test generation and management.

---

## Environment Setup & Installer (For Future Implementation)

**Note:** OS detection and automatic Playwright/dependency setup will be implemented after the agent core is validated and working reliably.

- The agent should detect the user's OS (Windows, macOS, Linux) at runtime using Python's `platform` module.
- The agent should check for Playwright and browser dependencies on first run.
- Recommended: Bundle Python dependencies and Playwright browsers in the installer (using PyInstaller or similar), but also support fallback to download/install on first run if needed.
- This ensures a "just works" experience for users, but is best added after the core agent is stable.
- Rationale: Deferring this step allows for faster iteration and debugging during early development. Once the agent is robust, packaging and environment automation can be added for production readiness.

---

## How the Application Map Works (End-to-End Guide)

### 1. User Flow
- **User provides:** Main URL, login details, and scan parameters via the web app.
- **Web app triggers scan:** Sends all details (with sensitive info encrypted) to the local agent.

### 2. Local Agent Responsibilities
- **Decrypts credentials** locally (never sends unencrypted sensitive data externally).
- **Navigates to the main URL** and performs login if needed.
- **Crawls the entire website** (all reachable pages after login), using provided credentials as needed.
- **Extracts all elements** on each page, collecting:
  - All possible locators (id, name, data-test-id, aria, text, etc.)
  - Best unique CSS and XPath selectors (shortest, most robust, unique)
  - Other attributes (type, description, bounding box, interactivity, etc.)
- **Detects PII** in element text/attributes, replaces with placeholders, and stores the mapping **locally and encrypted** (for later use in test execution).
- **Captures screenshots** for every page (for future visual testing).

### 3. Application Map Output
- **Stores a comprehensive map** of the application, including:
  - All pages, elements, locators, best selectors, PII placeholders, screenshots, etc.
- **Keeps PII mapping and sensitive data local and encrypted.**

### 4. Test Step Generation
- **When user wants to generate a test case:**
  - User provides requirements and the target URL/page.
  - The system does **keyword matching** between the requirements and the application map (for now; NLP/semantic search later).
  - Selects the best possible locators for each step (can send multiple locators to LLM for flexibility).
  - LLM returns test steps with mapped actions and elements, referencing the application map.

### 5. Handling Transitions
- **If a test step involves a page transition:**
  - The agent finds the transition in the application map.
  - Selects elements from the new page for subsequent steps.

### 6. Test Execution
- **When executing test steps:**
  - Uses the application map to find the right elements and locators.
  - Replaces PII placeholders with real data (from local mapping or user-uploaded test data).
  - Executes steps using Playwright.

### 7. Visual Testing (Future)
- **Screenshots** are used for later visual regression/comparison.

### 8. Security & Traceability
- **Security:** All sensitive data (credentials, PII) is encrypted and never leaves the user's machine unprotected.
- **Extensibility:** The map is designed to support advanced features (NLP, visual testing, etc.) in the future.
- **Traceability:** Every test step and element is traceable back to the application map for robust, reliable automation.

---

## Implementation Phases

### 1. Core Functionality
- **Comprehensive Scanning:**
  - Crawl all reachable pages using Playwright.
  - Extract all relevant UI elements, skipping risky/non-UI tags.
- **Robust Locator Generation:**
  - For each element, generate multiple locators (id, data-test-id, text, role, name, placeholder, class, CSS, XPath).
  - Attempt to determine the "best" unique CSS and XPath selectors.
- **Intelligent Filtering:**
  - Exclude elements by tag, role, or other heuristics.
- **PII Sanitization:**
  - Use regex and keyword-based detection to flag and replace PII in extracted text.
- **Authentication & Navigation:**
  - Accept user-provided credentials/selectors for login.
  - Use Playwright to perform login and persist session.
  - Optionally, fill forms with dummy data to reach deeper pages.
- **Application Map JSON:**
  - Output a rich, structured JSON as described, including all new fields (see schema below).

### 2. Communication with Web App Backend
- **Progress Reporting:**
  - Use async HTTP (e.g., httpx) to POST progress updates to a backend endpoint.
  - Include app_id, status, current page, counts, and messages.
- **Final Data Upload:**
  - POST the completed application map to the backend for storage and LLM use.
- **Security:**
  - Ensure all sensitive data (credentials, PII) is handled securely and never logged or sent in plaintext.

### 3. Installer/Distribution
- **Packaging:**
  - Use PyInstaller or similar to create a standalone executable for Windows/Mac/Linux.
  - Bundle Playwright and all dependencies.
- **User Experience:**
  - Provide a simple installer or zip, with clear instructions.
  - On first run, prompt for any required config (API URL, credentials, etc.).
- **Auto-Update (Future):**
  - Consider a mechanism for agent updates (optional for MVP).

---

## Application Map JSON Schema (Sample)
```json
{
  "aut_id": "string",
  "scanned_at": "datetime_isoformat",
  "base_url": "string",
  "pages": [
    {
      "url": "string",
      "title": "string",
      "page_summary": "string",
      "elements": [
        {
          "unique_id": "string",
          "type": "string",
          "description": "string",
          "locators": [
            { "type": "string", "value": "string" }
          ],
          "best_unique_css": "string",
          "best_unique_xpath": "string",
          "attributes": { /* ... */ },
          "text_content": "string",
          "is_interactive": "boolean",
          "has_pii": "boolean",
          "bounding_box": { /* ... */ }
        }
      ]
    }
  ]
}
```

---

## Key Implementation Details

### Element Extraction & Filtering
- Use a broad selector for relevant elements (inputs, buttons, links, headings, etc.).
- Exclude risky tags: script, style, meta, link, base, title, noscript.
- Ignore elements with roles like "presentation" or "none".
- Handle iframes and dynamic content.

### Locator Generation
- Prioritize: data-test-id, id, text, role, name, placeholder, class.
- Generate and test uniqueness for CSS/XPath selectors.
- Use Playwright's JS evaluation for advanced selector logic if needed.

### PII Detection & Sanitization
- Use regex for emails, phones, SSNs, etc.
- Flag and replace detected PII with placeholders.
- Maintain a `has_pii` flag for each element.
- Store PII mapping locally and encrypted for later use in test execution.

### Authentication & Navigation
- Accept login details from user/frontend.
- Use Playwright to perform login and persist session (storage_state).
- Optionally, fill forms with dummy data to reach deeper pages.

### Progress Reporting
- POST progress updates to backend endpoint with app_id, status, current page, counts, and messages.
- On completion, POST the full application map.

### Error Handling & Resilience
- Log errors locally, but continue scanning where possible.
- Report critical failures to backend.
- Deduplicate and canonicalize URLs.
- Add rate limiting between requests.
- Allow user to specify scan scope (include/exclude patterns).

### Optional Enhancements
- Capture screenshots for each page.
- Support concurrent page scans for speed.
- Auto-update mechanism for agent.

---

## Best Practices & Considerations
- **Security:** Never log or transmit sensitive data in plaintext.
- **Performance:** Balance thoroughness with scan speed and resource usage.
- **User Experience:** Provide clear progress and error feedback.
- **Extensibility:** Design for future enhancements (semantic search, advanced PII detection, etc.).

---

## Next Steps
1. Scaffold the local agent project and set up Playwright.
2. Implement core scanning and extraction logic.
3. Add backend communication for progress and results.
4. Package as an installer for distribution.

---

*This document is a living reference. Update as requirements and implementation evolve.* 