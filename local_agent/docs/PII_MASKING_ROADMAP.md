# PII Masking & Privacy Roadmap

## Vision Statement

**Our solution is built on two core principles:**
1. **Privacy of user data:** No user-entered or sensitive data is ever extracted, stored, or sent to the cloud/AI. All PII detection and masking is performed locally, ensuring that user data never leaves the user's system.
2. **Local execution:** All scanning, masking, and test generation logic runs on the user's machine. Even though our solution is AI-powered, core data privacy is never compromised.

---

## Current State (MVP)
- Attribute-value-only scanning (never keys)
- No extraction of `value` for any element (input, textarea, select, or otherwise)
- Microsoft Presidio (NLP + regex) for PII detection
- Sophisticated heuristics to prevent over-masking
- Contextual fake value generation (Faker)
- Real→fake mapping for traceability
- Transparent annotation (`has_pii`, `fake_values`)
- No hardcoded whitelists
- Audit-ready, extensible, and scalable

---

## Short-Term Roadmap (Next 1-2 Releases)

1. **Per-Entity-Type Confidence Thresholds**
   - Allow different Presidio confidence thresholds for different PII types (e.g., PERSON, DATE, LOCATION).
   - Make thresholds configurable and document them for compliance.

2. **Custom Fake Value Formatting**
   - Support format-matching for phone numbers, emails, and other structured PII.
   - Allow user-defined fake value templates for advanced use cases.

3. **Internationalization & Locale Awareness**
   - Add support for local Faker providers (e.g., Indian PAN/Aadhaar, EU VAT).
   - Allow locale to be set per scan or per field.
   - Add custom regexes and fake generators for non-Western PII types.

4. **Versioned Masking & Audit Logs**
   - Add a `masking_version` or `masking_rules_applied` field to each mapping/log entry.
   - Ensure all masking decisions are traceable to the ruleset used.

5. **Small, Audited Exclusion List (if needed)**
   - Maintain a carefully managed list for high-frequency UI false positives (e.g., "Quantity").
   - Keep this list minimal and auditable.

---

## Medium-Term Roadmap (3-6 Months)

6. **Token Tagging (Optional)**
   - Allow optional `[PII_TYPE]` token tagging for LLM post-processing or redaction use cases.

7. **Selective Default Value Handling**
   - Optionally include non-PII default values (e.g., currency symbols, static dates) for LLM/test context, with strict audit controls.

8. **API/Service Wrapping**
   - Expose masking logic as a local service with API endpoints (mask/unmask).
   - Support masking "profiles" (e.g., full obfuscation vs. LLM-friendly).

9. **Benchmarking & Monitoring**
   - Build tools to benchmark masking accuracy, performance, and false positive/negative rates.
   - Monitor masking decisions and log statistics for ongoing tuning.

---

## Long-Term Vision

- **Zero Trust, Local-First AI:**
  - All AI-powered test generation and PII masking runs locally. No user data is ever sent to the cloud or external LLMs.
  - Users can trust that their sensitive data is never exposed, even as AI capabilities expand.

- **Compliance Leadership:**
  - Maintain best-in-class compliance documentation, audit logs, and privacy guarantees.
  - Proactively adapt to new privacy regulations and enterprise requirements.

- **Continuous Improvement:**
  - Regularly review heuristics, thresholds, and exclusion lists based on real-world feedback and expert input.
  - Stay ahead of the curve in privacy engineering and AI-powered test automation.

---

## How We Deliver on Our Promise
- **All masking and test generation logic runs locally.**
- **No user data is ever sent to the cloud or external AI.**
- **All compliance, audit, and privacy documentation is maintained and versioned.**
- **We welcome external expert review and continuous improvement.**

---

*This roadmap is stored alongside all PII compliance documentation for transparency, auditability, and product planning.* 