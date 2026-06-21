# NovaScript Quickstart

This guide gives new users a five-minute path through the NovaScript trust lifecycle.

## 1. Generate Artifact

Call NovaScript generation:

```http
POST /v1/novascript/generate
```

Minimal request:

```json
{
  "prompt": "Create a governed deployment readiness check",
  "project_id": "project-employee-rbac",
  "language": "python",
  "mode": "analysis"
}
```

Result includes engineering output plus trust artifacts:

```text
governance_receipt
certificate_chain
policy_decision
formal_assurance_report
portable_verification_package
```

## 2. Issue Receipt

Receipt issuance happens during governed generation. The receipt proves a governed decision occurred.

Required receipt fields:

```text
receipt_id
organization_id
project_id
prompt_hash
output_hash
trust_score
status
sequence
signature
```

## 3. Verify Receipt

Use the SDK:

```python
from afritech.sdk import verify_receipt

result = verify_receipt(receipt)
```

Or use the API:

```http
POST /v1/novascript/receipts/verify
```

## 4. Validate Artifact

Use the universal validation API:

```http
POST /v1/novascript/validate/artifact
```

Example:

```json
{
  "artifact_type": "governance_receipt",
  "artifact": {
    "receipt_id": "rcpt-...",
    "organization_id": "org-alpha",
    "project_id": "project-payments",
    "prompt_hash": "sha256-prompt",
    "output_hash": "sha256-output",
    "trust_score": 92,
    "status": "approved",
    "sequence": 1,
    "signature": "sha256-signature"
  }
}
```

SDK equivalent:

```python
from afritech.sdk import validate_artifact

result = validate_artifact({
    "artifact_type": "governance_receipt",
    "artifact": receipt,
})
```

## 5. Publish Trust Proof

Use public verification endpoints:

```http
GET /public/trust/{receipt_id}
GET /public/trust/{receipt_id}/package
GET /public/certificates/{certificate_id}
GET /public/assurance/{report_id}
```

## Result

After this flow, an external party can verify:

```text
receipt validity
certificate presence
assurance report presence
portable package offline-readiness
```

## Boundary

Quickstart verification proves artifact integrity and NovaScript trust evidence. It does not grant production authority, replace legal audit, or redefine proof truth.
