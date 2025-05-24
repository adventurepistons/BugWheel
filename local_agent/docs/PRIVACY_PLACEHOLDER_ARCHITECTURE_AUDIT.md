Privacy-First LLM-Driven Test Automation Using Placeholders

1. Introduction
This document describes a privacy-preserving approach for automated UI test generation and execution using Large Language Models (LLMs), a custom Domain-Specific Language (DSL), and a local agent. The core principle is that no real test data or PII (Personally Identifiable Information) is ever exposed to the LLM, web application, or any cloud service. All sensitive data is abstracted using standardized placeholders defined in a DSL.

2. Key Principles
- No real or fake test data is ever used in the web app, LLM, or application map.
- All user input, application mapping, and LLM interaction use only placeholders.
- Real data is only used locally, on the user's system, at test execution time.
- The placeholder list is centrally defined in a DSL and synchronized between the web app and local agent.

3. Terminology
- Web UI: The user-facing interface for test step input and LLM integration.
- UI Element Map: The output of the local agent's scan, listing all UI elements with placeholders.
- Placeholder: A standardized token (e.g., [EMAIL], [PASSWORD]) representing a type of sensitive data.

4. Workflow Overview
A. DSL and Placeholders
- A DSL defines a set of standardized placeholders for all types of sensitive/test data (e.g., [EMAIL], [PASSWORD], [USERNAME], [PHONE], etc.).
- Users are instructed to use only these placeholders in all test steps and requirements.

B. Application Mapping (Local Agent)
- The local agent scans the target web application.
- All detected PII or sensitive data in the UI is replaced with the appropriate placeholder (not with fake data).
- The resulting UI Element Map contains only placeholders in all relevant fields (e.g., text_content, description, xpath, etc.).
- The local agent only needs the placeholder list (not the full DSL) for this masking.

C. Test Step Input
- Users write test steps or requirements using only placeholders (never real or fake data).
- Example: "Login as [EMAIL] with password [PASSWORD]"

D. Element Matching (Web UI)
- The Web UI uses proprietary logic to match user test steps (with placeholders) to potential UI elements in the UI Element Map (also with placeholders).
- This matching is straightforward, as both sides use the same placeholder vocabulary.

E. LLM Interaction
- The Web UI sends the test step (with placeholders) and the list of potential elements (with placeholders) to the LLM.
- The LLM is prompted to treat placeholders as real data and generate structured test cases using only placeholders.
- No real or fake data is ever sent to the LLM.

F. Test Script Generation
- The Web UI generates a test script using only placeholders.
- The script is sent to the local agent for execution.

G. Test Execution (Local Agent)
- The local agent receives the script and, at execution time, replaces all placeholders with real values from user-provided test data.
- This mapping and substitution happen locally and are never exposed externally.
- The agent executes the test using the real data.

5. Data Flow
User Input (Placeholders)
    |
    v
Web UI (Placeholders)
    |
    v
UI Element Map (Placeholders) <--- Local Agent (scans & masks with placeholders)
    |
    v
LLM (Placeholders only)
    |
    v
Test Script (Placeholders)
    |
    v
Local Agent (Replaces placeholders with real data at execution)
    |
    v
Test Execution (Real data, local only)

6. Compliance Alignment
This system is designed to support compliance with:
- GDPR (Articles 5 & 25): No personal data is processed by cloud or LLM services.
- HIPAA (Privacy & Security Rule): Real user data remains on the user's device; test execution is isolated.
- SOC 2: System architecture supports secure access, auditability, and confidentiality.

7. Security Implementation
- Local agent uses encryption-at-rest for all temporary files.
- All sensitive data is stored in memory only for the duration of execution and securely deleted after use.
- No logging of PII at any layer.
- Optional: Agent config file supports data_retention: false for strict ephemeral mode.

8. Placeholder Definitions
Placeholders are defined in a versioned JSON schema, e.g.:
{
  "placeholders": {
    "EMAIL": { "type": "string", "format": "email", "description": "Generic email address placeholder" },
    "PASSWORD": { "type": "string", "minLength": 8, "description": "Password placeholder" }
  }
}
- The placeholder list is versioned and synchronized between the Web UI and local agent.

9. Dual Use of DSL in the Platform
- The DSL is used in two main places:
  1. Placeholder enforcement in object mapping (application map): Only the placeholder registry is used to ensure all PII is replaced with standardized placeholders.
  2. Full DSL-driven test step authoring and LLM mapping: The complete DSL (keywords, actions, templates, placeholders) is used for authoring and mapping test steps, with privacy validation before LLM processing.

10. Central Repository and Synchronization
- The placeholder registry and DSL schema are maintained in a central backend repository.
- The local agent and other components fetch the latest version to ensure consistency and compliance.

11. Certification Readiness
The system is designed for high compliance and minimal privacy exposure. For enterprise deployment, we recommend:
- Privacy Impact Assessment (PIA)
- Penetration Testing of the local agent
- SOC 2 Type I audit
- Self-assessment via GDPR Toolkit or NIST Privacy Framework

12. Implementation Details
A. DSL and Placeholder Management
- The DSL defines all placeholders and their intended use.
- Both the Web UI and local agent reference the same placeholder list (JSON, YAML, or similar).
- Placeholders are standardized and versioned.

B. Local Agent Masking Logic
- On scanning, the agent detects PII and replaces it with the appropriate placeholder.
- All fields (including nested fields like locators, descriptions, etc.) are masked recursively.
- No fake data generation is needed.

C. LLM Prompt Engineering
- LLM prompts include only placeholders.
- The LLM is instructed to treat placeholders as real data and use them in generated test steps/scripts.
- Example prompt: 
  Given the step 'Login as [EMAIL] with password [PASSWORD]' and these elements: ...

D. Test Execution
- The local agent receives the script with placeholders.
- At execution time, the agent replaces placeholders with real values from user-provided test data.
- This mapping is local and never leaves the user's system.

13. Security and Privacy Considerations
- No real or fake data is ever sent to the LLM, Web UI, or stored in the UI Element Map.
- All mapping and substitution of real values happens only on the local agent.
- The local agent should securely handle and delete real test data after execution.
- No logs or outputs should contain real data.

14. Example End-to-End Flow
1. User Input: 
   "Login as [EMAIL] with password [PASSWORD]"
2. UI Element Map (element): 
   {
     "text_content": "[EMAIL]",
     "description": "[EMAIL] [EMAIL] li",
     "xpath": "//li[normalize-space(text())='[EMAIL]']"
   }
3. LLM Prompt: 
   - Test step: "Login as [EMAIL] with password [PASSWORD]"
   - Elements: (with [EMAIL] in their fields)
4. LLM Output: 
   - Structured test case using placeholders.
5. Script Generation: 
   - Script with placeholders.
6. Local Agent Execution: 
   - Replaces [EMAIL] and [PASSWORD] with real values from user's test data.

15. Potential Challenges and Mitigations
- User Error: Users must be trained to use only placeholders in test steps.
  Mitigation: Enforce placeholder usage in the UI and validate input.
- Placeholder Drift: Placeholder definitions must be kept in sync between Web UI and local agent.
  Mitigation: Use a versioned, shared placeholder list.
- Complex Data Types: For complex or custom data, extend the DSL and placeholder set as needed.

16. Future Enhancements
- Dynamic Placeholder Detection: Automatically suggest or enforce placeholders in user input.
- Placeholder Validation: Validate that all test steps and scripts use only approved placeholders.
- User-Defined Placeholders: Allow users to define custom placeholders for special cases.
- Automated DSL Synchronization: Ensure the placeholder list is always up-to-date across all components.

17. Summary Table
Step                | Data Used         | Privacy Level      
---------------------|-------------------|--------------------
User Input          | Placeholders      | No PII             
UI Element Map      | Placeholders      | No PII             
LLM Interaction     | Placeholders      | No PII             
Script Generation   | Placeholders      | No PII             
Local Agent         | Real Data         | Local Only         

18. Certification Readiness
The system architecture and methodology outlined here are inherently designed for high compliance and minimal privacy exposure. With minimal adjustments, the platform can pass internal and external reviews for GDPR, HIPAA, and SOC 2 readiness. Independent assessment or audits (PIA, PenTest, ISO 27001 readiness) are recommended for final deployment in enterprise environments.

19. Conclusion
This approach ensures maximum privacy, regulatory compliance, and ease of use for LLM-driven test automation. By using placeholders at every stage except local execution, you eliminate the risk of exposing sensitive data while maintaining a robust and flexible workflow.

---
This document is intended for expert, audit, and compliance review. Please provide feedback for further refinement and certification readiness.

20. Enhanced Placeholder Schema and User Training
- The placeholder registry now uses an enhanced schema (see backend/dsl/placeholders.schema.json) with rich metadata for each PII type.
- The registry (backend/dsl/placeholders.json) is centrally managed, versioned, and validated.
- The placeholder list is available for user training, onboarding, and compliance documentation. It can be used to generate user-facing training materials and reference pages.
- The process for maintaining and updating the registry includes expert review, schema validation, and regular audits.

21. Edge-Case and Sensitive PII Placeholders
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