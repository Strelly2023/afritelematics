# NovaScript Adoption Guide

This guide turns NovaScript from an internal platform into an ecosystem integration path.

## Step 1: Install SDK

Use the in-repo Python SDK:

```python
from afritech.sdk import validate_artifact, verify_receipt
```

## Step 2: Generate Artifacts

Use NovaScript or an external tool to produce engineering and trust artifacts.

Required artifacts:

```text
governance receipt
certificate chain
policy decision
assurance report
```

## Step 3: Validate Artifacts

Use SDK validation:

```python
result = validate_artifact({
    "artifact_type": "governance_receipt",
    "artifact": receipt,
})
```

Or use the universal API:

```http
POST /v1/novascript/validate/artifact
```

## Step 4: Join Federation

Onboard an organization:

```http
POST /v1/novascript/organizations/onboard
```

Publish trust exchange:

```http
POST /v1/novascript/federation/trust-exchange
```

Inspect trust graph:

```http
GET /v1/novascript/trust/graph
```

## Step 5: Publish Trust Proofs

Use public verification endpoints:

```http
GET /public/trust/{receipt_id}
GET /public/trust/{receipt_id}/package
GET /public/certificates/{certificate_id}
GET /public/assurance/{report_id}
```

## Adoption Outcomes

Organizations can progress through:

```text
NovaScript Verified
NovaScript Trusted
NovaScript Certified
```

## Integration Modes

```text
Validation-only:
External system generates artifacts; NovaScript verifies them.

Full pipeline:
External system uses NovaScript generation and trust outputs.

Audit-only:
External verifier submits audit packages for validation.
```
