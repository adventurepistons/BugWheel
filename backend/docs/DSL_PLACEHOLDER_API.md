# DSL Placeholder Registry API Documentation

This document describes the REST API endpoints for accessing the centrally managed PII placeholder registry and schema. These endpoints are used by the local agent, web UI, and other services to ensure consistent, up-to-date privacy masking and validation.

---

## 1. Get Latest Placeholder Registry

**Endpoint:**
```
GET /api/dsl/placeholders/latest
```

**Description:**
Returns the latest version of the PII placeholder registry (`placeholders.json`). This file contains all supported PII placeholders and their metadata, used for privacy masking, validation, and user training.

**Response:**
- `200 OK`
- Content-Type: `application/json`
- Body: JSON object (see `backend/dsl/placeholders.json`)

**Example Usage:**
```bash
curl http://localhost:8000/api/dsl/placeholders/latest
```

---

## 2. Get Placeholder Schema

**Endpoint:**
```
GET /api/dsl/placeholders/schema
```

**Description:**
Returns the JSON schema (`placeholders.schema.json`) that defines the structure and required metadata for all placeholders. Use this for validation, tooling, and to ensure all placeholder entries are consistent and compliant.

**Response:**
- `200 OK`
- Content-Type: `application/json`
- Body: JSON schema (see `backend/dsl/placeholders.schema.json`)

**Example Usage:**
```bash
curl http://localhost:8000/api/dsl/placeholders/schema
```

---

## Integration Points
- **Local Agent:** Fetches the latest placeholder list for PII masking and validation.
- **Web UI:** Uses the registry for user input validation, auto-complete, and user training/reference.
- **Developers:** Use the schema to validate new or updated placeholder entries before deployment.
- **Documentation/Training:** The placeholder list can be used to generate user-facing documentation and onboarding materials.

---

## Change Management & Versioning
- The placeholder registry and schema are centrally managed and versioned in `backend/dsl/`.
- All updates should be validated against the schema before deployment.
- Regular expert review and audits are recommended.

---

## File Locations
- **Registry:** `backend/dsl/placeholders.json`
- **Schema:** `backend/dsl/placeholders.schema.json`

For further details, see DSL and privacy documentation in `local_agent/docs/`. 