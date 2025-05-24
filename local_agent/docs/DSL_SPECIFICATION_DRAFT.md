DSL Specification Draft: Privacy-First, Placeholder-Driven Test Automation

1. Overview
This specification defines a Domain-Specific Language (DSL) for authoring, validating, and compiling test cases in a privacy-first, LLM-driven test automation platform. The DSL enforces placeholder-only usage for all test data, supports both structured and natural language input, and is designed for extensibility, compliance, and developer productivity.

2. Schema Structure
The DSL is defined in a versioned JSON Schema (or YAML) file, which includes:
- dsl_version: Semantic version of the schema
- actions: Registry of supported actions, with requirements and validation
- elements: Registry of UI elements, selectors, and states
- states: List of supported element states/modifiers
- placeholders: Centralized, versioned registry of all allowed placeholders
- templates: Pre-built, compliant test step patterns
- compliance: Compliance and audit configuration

Example Top-Level Structure:
{
  "dsl_version": "1.0.0",
  "actions": { ... },
  "elements": { ... },
  "states": [ ... ],
  "placeholders": { ... },
  "templates": [ ... ],
  "compliance": { ... }
}

3. Placeholder Registry
- All test data values must be represented as placeholders (e.g., [EMAIL], [PASSWORD], [PHONE_NUMBER]).
- Placeholders are centrally defined, versioned, and validated.
- Each placeholder includes:
  - type: Data type (string, number, etc.)
  - format: (optional) Format hint (email, phone, etc.)
  - description: Human-readable description
  - category: (optional) e.g., authentication, contact
  - security_level: e.g., pii, sensitive
  - examples: (optional) Example values
  - validation_regex: (optional) Regex for validation
  - faker_provider: (optional) Hint for fake data generation (if needed)

Example:
{
  "EMAIL": {
    "type": "string",
    "format": "email",
    "description": "Email address placeholder",
    "category": "authentication",
    "security_level": "pii",
    "examples": ["user@example.com"],
    "validation_regex": "^\\[EMAIL\\]$",
    "faker_provider": "email"
  },
  "PASSWORD": {
    "type": "string",
    "minLength": 8,
    "description": "Password placeholder",
    "faker_provider": "password"
  }
}

4. Actions
- Each action is defined with:
  - requires: List of required fields (e.g., element, value)
  - optional: List of optional fields (e.g., state)
  - validation: (optional) Custom validation rules
  - description: Human-readable description

Example:
{
  "click": {
    "requires": ["element"],
    "optional": ["state"],
    "description": "Click on an element"
  },
  "enter": {
    "requires": ["element", "value"],
    "validation": "value_must_be_placeholder",
    "description": "Enter value into an element"
  }
}

5. Elements
- Each element is defined with:
  - selectors: List of supported selector types (e.g., text, id, class)
  - states: List of valid states for the element
  - description: (optional) Human-readable description

Example:
{
  "button": {
    "selectors": ["text", "id", "class"],
    "states": ["visible", "enabled", "clickable"],
    "description": "Button element"
  },
  "input": {
    "selectors": ["name", "id", "placeholder"],
    "states": ["visible", "enabled", "focused"],
    "description": "Input field"
  }
}

6. States
- List of valid states/modifiers for elements (e.g., visible, enabled, checked).

Example:
["visible", "enabled", "checked", "selected", "focused"]

7. Templates
- Pre-built, compliant test step patterns for rapid authoring and LLM prompting.
- Templates use placeholders and can be used for auto-completion and validation.

Example:
[
  "Login as [EMAIL] with password [PASSWORD]",
  "Click [BUTTON] to submit",
  "Verify [ELEMENT] is [STATE]"
]

8. Compliance and Audit
- Configuration for compliance features:
  - pii_validation: true/false (enforce anti-PII rules)
  - audit_logging: true/false (log placeholder usage and validation events)
  - retention_policy: e.g., local_only, ephemeral

Example:
{
  "pii_validation": true,
  "audit_logging": true,
  "retention_policy": "local_only"
}

9. Versioning and Synchronization
- The DSL schema and placeholder registry are versioned using semantic versioning.
- Each file includes dsl_version, min_compatible, and (optionally) migration guides.
- All components (UI, local agent, LLM integration) must sync to the same version.
- Provide an API endpoint (e.g., /api/dsl-schema/latest) for clients to fetch the current schema.

10. Validation Rules
- All values for test data must match an approved placeholder (e.g., [EMAIL]).
- No real or fake data is allowed in any test step or value.
- The validator must flag unknown or unregistered placeholders.
- Action/element compatibility must be enforced (e.g., "enter" requires both element and value).
- Provide granular error messages and suggestions for invalid input.

11. Extensibility
- The DSL schema is modular: actions, elements, states, and placeholders can be extended independently.
- Support for user/org/project-defined placeholders, with validation and scoping.
- Allow for additional metadata fields (e.g., examples, description, faker_provider) for future AI/LLM-driven features.

12. Developer Experience
- Provide syntax highlighting, auto-completion, and real-time linting in the UI.
- Offer a CLI and web-based validator for DSL input.
- Template libraries for common test steps.

13. LLM and Test Case Integration
- LLM prompts should be generated from the DSL schema, using placeholders.
- The DSL-to-test compiler translates DSL input to structured test case format for execution.
- Example DSL input:
  "Enter [EMAIL] in the email input"
  "Click on the login button"
  "Verify that dashboard is visible"
- Example internal representation:
[
  { "action": "enter", "element": "input", "target": "email", "value": "[EMAIL]" },
  { "action": "click", "element": "button", "target": "login" },
  { "action": "verify", "state": "visible", "target": "dashboard" }
]

14. Security and Compliance
- The DSL schema and validators must enforce anti-PII rules (e.g., regex/static analysis for hardcoded sensitive data).
- All placeholder usage and validation events should be auditable.
- The schema should be open for review and, optionally, open-sourced for trust and adoption.

15. Directory Structure (Recommended)
dsl/
├── schema/
│   ├── dsl-core.json
│   ├── placeholders.json
│   ├── actions.json
│   ├── elements.json
│   └── templates.json
├── validators/
│   └── validate_step.py
├── compilers/
│   └── to_test_case.py
└── examples/
    └── login_step.dsl

16. Migration and Adoption
- Provide migration guides and backward compatibility for existing test cases.
- Offer training and documentation for users and developers.
- Plan for open-sourcing and community engagement.

17. Summary
This DSL specification provides a robust, extensible, and privacy-first foundation for LLM-driven test automation. It enforces placeholder-only usage, supports both structured and natural language input, and is designed for compliance, developer experience, and future AI integration.

18. Future Enhancement: Locator Hinting
To further improve the precision of element selection and LLM-driven mapping, the DSL may support an optional `locator_hint` field in the future. This field allows test authors or the DSL parser to specify a preferred locator type (e.g., "id", "text", "aria-label", "css", "xpath") for a given element reference. This can be inferred from the DSL input or explicitly provided.

Example:
{
  "action": "click",
  "element": "button",
  "target": "login",
  "locator_hint": "text"
}

This feature is not required for initial implementation but is recommended for future extensibility as LLM and automation capabilities evolve.

19. Dual Use Cases for DSL
The DSL serves two primary purposes in the platform:

1. Placeholder Enforcement in Object Mapping (Application Map)
- When scanning and mapping UI elements, only the placeholder registry is used.
- All detected or potential PII values in the application map are replaced with standardized placeholders (e.g., [EMAIL], [PHONE_NUMBER]).
- This ensures that no real or fake data is present in the object map, only placeholders from the centrally managed registry.
- The local agent fetches the latest placeholder list from a central backend repository to stay up to date.

2. Full DSL-Driven Test Step Authoring and LLM Mapping
- For test step authoring, the full DSL is used: keywords, actions, templates, and placeholders.
- User-authored steps are only checked for privacy (PII, placeholder enforcement) before being sent to the LLM.
- The LLM receives the raw, privacy-checked step and the list of potential elements, and is responsible for mapping the step to structured actions/elements/values using placeholders.
- This approach maximizes LLM flexibility and semantic power, while maintaining strict privacy boundaries.

20. Central Repository and Synchronization
- The DSL (especially the placeholder registry) is maintained in a central backend repository.
- The local agent and other components fetch the latest version as needed, ensuring consistency and auditability.
- Versioning and migration guides are provided for backward compatibility.

21. Enhanced Placeholder Schema and Registry
- The placeholder registry now uses an enhanced JSON schema (see backend/dsl/placeholders.schema.json) supporting rich metadata for each PII type.
- Metadata fields include: type, format, category, jurisdiction, industry, security_level, sensitivity_score, regulatory_scope, data_classification, retention_category, geographic_restrictions, cross_border_restrictions, anonymization_method, description, examples, validation_pattern, related_placeholders, compliance_notes, masking_method_hint, faker_provider, regex_pattern, is_detectable, notes.
- The registry is centrally managed and versioned. All components validate against the schema to ensure consistency and compliance.
- The placeholder list (backend/dsl/placeholders.json) is available for user training, onboarding, and reference. It can be used to generate user-facing documentation and training pages.
- The process for adding/updating placeholders includes expert review, schema validation, and versioning.

22. Edge-Case and Sensitive PII Placeholders
- The placeholder registry now includes additional placeholders for edge-case and sensitive PII types, such as:
  - ORGANIZATION_NAME: Organization or company name (contextually PII if unique)
  - UPLOADED_FILE: User-uploaded file (may contain PII)
  - FILE_METADATA: Metadata from uploaded files (e.g., EXIF, PDF properties)
  - SESSION_ID: Session identifier (may be sensitive/regulated)
  - API_KEY: API key or secret (may be sensitive/regulated)
  - ACCESS_TOKEN: Access or refresh token (may be sensitive/regulated)
  - CUSTOMER_LEGACY_ID: Internal or legacy customer/account identifier (contextually PII)
- The registry is regularly reviewed and updated to ensure coverage of all PII types detectable by Presidio, spaCy, regex, and other detection methods.
- These additions support full compliance, robust privacy masking, and comprehensive user training/documentation.

---
This draft is intended for expert, audit, and implementation review. Please provide feedback and suggestions for the next iteration. 