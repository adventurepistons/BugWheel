# Privacy & Data Protection Statement: Application Map Creation

## Our Commitment to Your Privacy

We understand that privacy and data protection are critical when scanning and mapping your web applications. Our local agent is designed from the ground up to ensure that your sensitive data is never exposed, extracted, or sent outside your environment.

---

## How We Protect Your Data

### 1. **No User Data Extraction**
- **We never extract or store any user-entered data.**
- The agent does not collect the contents of form fields, passwords, or any information typed or submitted by users.

### 2. **No Value Extraction for Any Element**
- The agent skips the `value` attribute for all elements (including input fields, textareas, selects, and others).
- This means that even default or pre-filled values are never collected or stored.

### 3. **Local-Only Processing**
- All scanning, analysis, and data processing happens entirely on your machine.
- No data is ever sent to the cloud, external servers, or third-party services.

### 4. **PII Detection & Masking**
- The agent uses advanced privacy technology (Microsoft Presidio and spaCy NLP) to detect and mask any sensitive information that might appear in static attributes (like labels, placeholders, or IDs).
- If any sensitive data is detected, it is replaced with a realistic fake value before being stored in the application map.

### 5. **No Hardcoded Whitelists**
- The system uses patterns and intelligent heuristics to avoid over-masking and to ensure only true sensitive data is protected.

### 6. **Encrypted Mapping for Traceability**
- Any mapping of real to fake values (for compliance or audit) is encrypted and stored locally, never leaving your system.

### 7. **Transparent Documentation & Auditability**
- All privacy logic, masking rules, and compliance documentation are available for review by your security, compliance, or legal teams.
- We welcome external audits and expert reviews.

---

## What Is Included in the Application Map
- Only non-sensitive, non-user-entered attributes (such as element IDs, names, labels, roles, and structure) are included.
- No user data, passwords, or field values are ever present in the map.
- The map is designed to help with automated testing and quality assurance, not to collect or expose any business or user data.

---

## For Compliance & Security Teams
- Our approach aligns with industry best practices for privacy, data minimization, and local-first security.
- We are happy to provide detailed technical documentation, expert reviews, and support for your compliance assessments.

---

**If you have any questions or require a privacy review, please contact our team.** 