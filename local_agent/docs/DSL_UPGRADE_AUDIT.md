DSL Upgrade and Design Audit Document

1. Introduction
This document is intended for expert review and feedback on the future direction of the Domain-Specific Language (DSL) used for test step authoring and automation in a privacy-first, LLM-driven test automation platform. The goal is to ensure the DSL is robust, extensible, and fully aligned with the placeholder-based privacy architecture.

2. Current State Analysis
- The existing DSL (see old/dsl) is keyword-driven, supporting actions (click, enter, verify), elements (button, field, input), and states (visible, enabled, etc.).
- It parses natural language commands and extracts actions, elements, values, and attributes.
- There is no built-in enforcement or validation of placeholder usage for sensitive/test data.
- Values can be any string, including real PII/test data, which is not privacy-compliant for the new architecture.

3. Requirements for the New/Upgraded DSL
A. Privacy and Placeholder Enforcement
- All test data values must be represented as placeholders (e.g., [EMAIL], [PASSWORD], [PHONE]).
- The DSL must validate that only approved placeholders are used in test steps and values.
- Placeholders should be centrally defined, versioned, and easily updatable.

B. Extensibility and Expressiveness
- The DSL should support a wide range of actions, elements, and states, and be easy to extend with new keywords or placeholders.
- Should support both structured and (optionally) natural language test step authoring.
- Should allow for user-defined/custom placeholders (with validation).

C. Integration and Synchronization
- The DSL (or at least the placeholder list) must be synchronized between the web UI, local agent, and any LLM prompt engineering logic.
- Versioning and backward compatibility should be considered.

D. Validation and User Experience
- The DSL should provide real-time validation and auto-completion in the UI to prevent user error.
- Should provide clear error messages and suggestions for invalid input.
- Should support template libraries for common test steps using placeholders.

E. Security and Compliance
- The DSL must never allow real or fake PII/test data in any test step or value.
- Should be auditable and easy to review for compliance.

4. Open Questions for Expert Review
- Should the DSL support both structured and natural language input, or only one?
- What is the best format for defining and sharing the placeholder list (JSON Schema, YAML, etc.)?
- How should user-defined placeholders be managed and validated?
- What is the best approach for versioning and synchronizing the DSL across components?
- Are there industry standards or best practices for privacy-first test automation DSLs?
- How can the DSL be made extensible for future AI/LLM-driven features?

5. Suggestions and Considerations
- Consider a JSON/YAML-based DSL definition with a clear schema for actions, elements, states, and placeholders.
- Implement a validation engine that enforces placeholder-only values and provides real-time feedback in the UI.
- Support for template libraries and auto-completion can improve user adoption and reduce errors.
- Ensure the DSL is modular and easy to update as new test automation or privacy requirements emerge.
- Plan for integration with LLM prompt engineering, so that the DSL can be used to generate context-aware prompts.
- Consider open-sourcing the DSL or aligning with industry standards for broader adoption and review.

6. Example Placeholder-Driven DSL Schema (for Discussion)
{
  "actions": ["click", "enter", "verify", "select"],
  "elements": ["button", "field", "input", "link"],
  "states": ["visible", "enabled", "checked"],
  "placeholders": {
    "EMAIL": { "type": "string", "format": "email", "description": "Email address placeholder" },
    "PASSWORD": { "type": "string", "minLength": 8, "description": "Password placeholder" }
  },
  "templates": [
    "Login as [EMAIL] with password [PASSWORD]",
    "Click [BUTTON] to submit"
  ]
}

7. Dual Use Cases for DSL
- The DSL is used for:
  1. Placeholder enforcement in object mapping (application map): Only the placeholder registry is used to ensure all PII is replaced with standardized placeholders.
  2. Full DSL-driven test step authoring and LLM mapping: The complete DSL is used for authoring and mapping test steps, with privacy validation before LLM processing.

8. Central Repository and Synchronization
- The placeholder registry and DSL schema are maintained in a central backend repository.
- The local agent and other components fetch the latest version to ensure consistency and compliance.

9. Next Steps
- Experts are invited to review this document and provide feedback on requirements, schema, validation, extensibility, and integration.
- Based on feedback, a detailed DSL specification and implementation plan will be developed.

10. Enhanced Placeholder Schema and Training
- The placeholder registry now uses an enhanced schema (see backend/dsl/placeholders.schema.json) with rich metadata for each PII type.
- The registry (backend/dsl/placeholders.json) is centrally managed, versioned, and validated.
- The placeholder list is available for user training, onboarding, and DSL documentation. It can be used to generate user-facing training and reference materials.
- The process for updating the registry includes expert review, schema validation, and regular audits.

11. Edge-Case and Sensitive PII Placeholders
- The placeholder registry now includes additional placeholders for edge-case and sensitive PII types, such as:
  - ORGANIZATION_NAME: Organization or company name (contextually PII if unique)
  - UPLOADED_FILE: User-uploaded file (may contain PII)
  - FILE_METADATA: Metadata from uploaded files (e.g., EXIF, PDF properties)
  - SESSION_ID: Session identifier (may be sensitive/regulated)
  - API_KEY: API key or secret (may be sensitive/regulated)
  - ACCESS_TOKEN: Access or refresh token (may be sensitive/regulated)
  - CUSTOMER_LEGACY_ID: Internal or legacy customer/account identifier (contextually PII)
- The registry is regularly reviewed and updated to ensure all PII types detectable by Presidio, spaCy, regex, and other detection methods are covered.
- This supports compliance, robust privacy masking, and comprehensive user training/documentation.

---
This document is intended for expert, audit, and architectural review. Please provide detailed feedback and suggestions for the next iteration of the DSL. 