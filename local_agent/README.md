# Local Agent

## Overview
The Local Agent is a standalone tool that scans a web application, builds a detailed application map, detects and replaces PII, captures screenshots, and reports progress/results to the backend. It is designed to work with a config file for easy setup and automation.

## Setup
1. Ensure Python 3.8+ is installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
3. Copy `config.example.json` to `config.json` and fill in your application details.
4. Run the agent:
   ```bash
   python agent.py
   ```

## Config File
- All scan and login details are provided via `config.json`.
- See `config.example.json` for required fields and structure.

## How It Works
1. Loads config and sets up logging.
2. Sets up Playwright browser and context.
3. Performs login if needed.
4. Crawls the application, extracting all relevant elements and locators.
5. Detects and replaces PII, storing mapping locally (encrypted).
6. Captures screenshots for every page.
7. Reports progress and errors to the backend.
8. Saves the application map, logs, and PII mapping.

## Login Automation
- The agent uses selectors and credentials from the config to perform login automatically.
- It navigates to the login page, fills in the username and password, and clicks the login button.
- Login success is determined by waiting for the page to load and (optionally) checking for a dashboard element or URL change.

## Crawling Logic
- The agent uses a breadth-first search (BFS) approach to crawl the application starting from the base URL.
- For each page, it extracts all links (`<a href=...>`) and adds them to the crawl queue.
- It respects `include_patterns` and `exclude_patterns` from the config to control which URLs are visited.
- The crawl stops when the maximum number of pages (`max_pages`) is reached.
- (Coming soon) For each page, the agent will extract elements and capture a screenshot.

## Best Locator Selection Logic
- The agent only considers unique locators with a score above a threshold (default 70) as candidates for the best locator.
- If no such locator is found, it falls back to the shortest unique relative XPath, then to the shortest unique relative CSS selector.
- If no unique locator is found, the element is marked as having no best locator (and will not be used for test case generation).
- **Non-unique locators are never used for test case generation.**
- This ensures test reliability and reduces flakiness.

## Feature Updates & Enhancements (Changelog)

### v0.2.x (Current)
- **Context-Aware PII Masking:**
  - Fake values are generated based on attribute and value context (e.g., emails for email fields, passwords for password fields, country codes for country fields, etc.).
  - No manual whitelist is needed; logic adapts to any field name or value.
  - Navigation labels and common UI terms are not masked unless they are actual PII (like an email or URL in a link).
  - Confidence threshold for masking is tunable (default: 0.5).
  - Debug logging for PII detection and masking decisions.

### v0.1.x
- **Robust Locator Extraction & Scoring:**
  - All possible locators (id, name, aria-label, class, text, value, placeholder, title, data-*, CSS, XPath) are generated for each element.
  - Each locator is scored for reliability and checked for uniqueness.
  - Only unique, high-scoring locators are used for test case generation.
  - Fallback to unique XPath or CSS if no high-score locator is unique.
- **Password Masking:**
  - All password input values are always masked, even if not detected as PII.
  - Passwords are replaced with realistic fakes using Faker.
- **PII Detection Pipeline:**
  - Uses Microsoft Presidio for robust, enterprise-grade PII detection (names, emails, phone numbers, SSNs, credit cards, addresses, etc.).
  - Combines regex, context, and NLP (spaCy) for maximum coverage.
  - Mapping of real→fake values is stored for traceability and test execution.
- **Fallback Logic:**
  - If no suitable fake value can be generated, a descriptive placeholder (e.g., `<PII:ENTITY_TYPE>`) is used.
- **Mapping File:**
  - All replacements are recorded in a mapping file for compliance, debugging, and test execution.
- **Encryption (Planned):**
  - Mapping file will be encrypted using a generated key (MVP) and optionally user-supplied passwords (future).
- **Multiple Scan Flows:**
  - Supports both public and authenticated scan flows, tagging results accordingly.
- **Application Map Annotation:**
  - Each element is annotated with `has_pii` and `fake_values` for transparency.
- **Scalability:**
  - Designed to scan thousands of sites daily with no manual list maintenance.

### Roadmap / Future Features
- **Mapping file encryption and user-supplied password support.**
- **Hybrid scan mode (guest + authenticated in one run).**
- **Custom/tunable Presidio recognizers and thresholds for specific domains.**
- **Advanced reporting and compliance dashboards.**
- **LLM-driven test step mapping and feedback loop.**

## Multiple Scan Flows (Public & Authenticated)
- The agent supports running multiple scan flows in sequence (e.g., public/guest and authenticated/user).
- Each flow is defined in the `scan_flows` section of the config. For public scans, set `login` to null. For authenticated scans, provide login details.
- The agent will run each flow, tagging results with the flow name.

### Example `scan_flows` config:
```json
"scan_flows": [
  { "name": "public", "login": null },
  { "name": "authenticated", "login": { ... } }
]
```

## Future Feature: Hybrid Scan
- In the future, the agent may support a hybrid scan mode, where it crawls each page both as a guest and as a logged-in user in a single run, and records which version is which.
- For now, use sequential scan flows for full coverage.

## Tagging Results by Scan Flow
- Each application map is tagged with the scan flow name (e.g., 'public', 'authenticated') and saved as a separate file.
- The tag is included as a top-level field in the JSON and in the filename.
- This allows you to distinguish between elements/pages available to guests vs. logged-in users, which is crucial for accurate test case creation and element matching later.

## PII Detection & Anonymization Plan

- **Detection:**
  - Use Microsoft Presidio for robust, enterprise-grade PII detection.
  - Presidio combines regex, context, and NLP (using spaCy as the default engine) to detect a wide range of PII types: email, phone, credit card, SSN, names, addresses, IPs, and more.
  - For any domain-specific PII not covered by Presidio, add custom regex recognizers.

- **Masking & Fake Value Generation:**
  - For each detected PII, generate a realistic fake value using Faker (for standard types) or a custom generator/placeholder for others.
  - Replace the PII in user-facing attributes (text, value, placeholder, aria-label) with the fake value.
  - Use descriptive placeholders (e.g., [EMAIL], [NAME]) only if a fake value cannot be generated.

- **Mapping & Annotation:**
  - Store a mapping of {real_value: fake_value} for all detected PII in a local, encrypted file.
  - For each element in the application map, annotate:
    - `has_pii` (True/False)
    - `pii_placeholders` or `fake_values` (list of what was replaced)
    - The masked/fake value in the element's text/attributes

- **Encryption:**
  - The PII mapping file is encrypted using a generated key stored locally (for MVP). Optionally, support user-supplied passwords for high-security use cases.

- **Test Execution:**
  - When running tests, use the mapping to substitute fake values with the real ones as needed.

- **Rationale:**
  - This approach maximizes privacy and security, while ensuring the LLM can still reason about the UI and generate realistic test steps.
  - The plan is extensible for future compliance, audit, and user requirements.

## Context-Aware PII Masking (v0.2+)

### Overview
The agent now uses a **context-aware PII masking pipeline** that combines advanced PII detection (via Microsoft Presidio) with smart, context-driven fake value generation. This ensures:
- Only true PII is masked.
- Fake values are as close as possible to the real data type (e.g., emails for email fields, passwords for password fields, country codes for country fields, etc.).
- No manual whitelist is needed, making the system scalable for large-scale SaaS use.

### How It Works
- For every element and attribute (e.g., `id`, `name`, `aria-label`, `placeholder`, `title`, `value`, `text_content`), the agent:
  1. Runs Presidio to detect PII, using a confidence threshold (default: 0.5).
  2. For each detected PII, checks the attribute name and value for context clues (e.g., "email", "password", "country").
  3. If context is clear, generates a fake value of the correct type (e.g., `fake.email()` for emails, `fake.password()` for passwords).
  4. If context is ambiguous, falls back to the entity type detected by Presidio.
  5. Navigation labels and common UI terms are not masked unless they are actual PII (like an email or URL in a link).
- All replacements are recorded in a mapping file for traceability and test execution.

### Example
| Attribute Name | Value         | Presidio Entity | What is Generated      |
|---------------|--------------|-----------------|-----------------------|
| email         | Email        | PERSON          | fake.email()          |
| password      | ConfirmPassword | PERSON        | fake.password()       |
| country       | US           | LOCATION        | fake.country_code()   |
| price         | 1200.00      | DATE_TIME       | fake price (number)   |
| label         | Register     | PERSON          | Register (not masked) |

### Benefits for Stakeholders, Developers, and Users
- **Privacy:** No real PII is ever exposed to the LLM, logs, or outputs.
- **Usability:** Fake values are realistic and context-appropriate, so LLMs and test generators can reason about the UI as if it were real.
- **Scalability:** No need to maintain a manual whitelist of field labels or terms, making the system robust for scanning thousands of sites.
- **Traceability:** All replacements are mapped for compliance, debugging, and test execution.

### How to Tune or Extend
- Adjust the confidence threshold in `pii_utils.py` to be more or less aggressive.
- Add more context rules for new field types as needed.
- Review the mapping and application map files to verify masking quality.

## Privacy Modes and Field Value Handling

By default, the local agent **does not extract the `value` attribute** for any element when building the application map. This ensures that real user-entered data (which may contain PII) and any default values are never collected or processed, maximizing privacy and compliance.

- **Static attributes** (such as `id`, `name`, `aria-label`, `placeholder`, `title`, etc.) are still extracted for robust locator mapping and LLM usability.
- **PII masking** is still applied to all extracted attributes, but the risk of leaking real user data is minimized by not collecting field values.

### Rationale
- **Default (private) mode**: Maximum privacy, no risk of collecting real user data from forms or default values.

See the code and comments in `playwright_utils.py` for details.

## Privacy-First PII Masking Strategy (2024+)

### Overview
The local agent implements a privacy-first approach to PII (Personally Identifiable Information) masking, ensuring that no real or fake PII ever leaves the user's machine. All sensitive data is abstracted using deterministic placeholders, and the mapping between real values and placeholders is stored locally in an encrypted format. This architecture guarantees zero PII exposure to the cloud, backend, or LLM, while enabling robust test automation and compliance.

### Key Principles
- **100% Local Masking:** All PII detection and masking is performed on the user's machine before any data is sent to the cloud or LLM.
- **Deterministic Placeholders:** Each unique PII value is replaced with a session-scoped, deterministic placeholder (e.g., `[EMAIL_1]`, `[NAME_2]`).
- **Local Mapping Storage:** The mapping between real PII values and placeholders is stored locally in an encrypted file, never transmitted or exposed externally.
- **Zero PII to Cloud/LLM:** Only masked data (with placeholders) is sent to the cloud backend or LLM for test step matching and script generation.
- **Remapping for Execution:** Before test execution, placeholders are remapped to real values locally, ensuring that real data is only used on the user's machine.

### Workflow Diagram
The following summarizes the privacy-first workflow:

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

### Compliance & Auditability
- **Audit Trail:** All masking and remapping actions are logged locally for compliance and debugging.
- **No PII Leakage:** The architecture is designed to meet and exceed regulatory requirements (GDPR, HIPAA, etc.) by ensuring no PII is ever exposed to third parties.
- **Extensible:** The placeholder registry and masking logic can be updated to cover new PII types and compliance needs.

### Benefits
- **Maximum Privacy:** No real or fake PII ever leaves the user's environment.
- **Enterprise-Ready:** Suitable for highly regulated industries (healthcare, finance, government).
- **Future-Proof:** Aligned with emerging privacy standards and zero-trust architectures.

---
*Update this file as new features are added or changed.* 