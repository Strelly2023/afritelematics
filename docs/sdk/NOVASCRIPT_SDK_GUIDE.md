# NovaScript SDK Guide

The NovaScript SDK exposes reference helpers for NTS v1 validation. These helpers are deterministic and can be used without running the NovaScript API server.

## Install Context

The SDK lives in:

```text
afritech.sdk.novascript
```

## Verify A Receipt

```python
from afritech.sdk import verify_receipt

result = verify_receipt(receipt)
```

Expected output:

```json
{
  "verified": true,
  "reason": "signature_match",
  "receipt_id": "rcpt-..."
}
```

## Verify An Audit Package

```python
from afritech.sdk import verify_audit_package

result = verify_audit_package({
    "receipt": receipt,
    "certificate_chain": certificate_chain,
})
```

Expected output:

```json
{
  "mode": "external_audit_verification",
  "verified": true
}
```

## Validate A Certificate Chain

```python
from afritech.sdk import validate_certificate_chain

result = validate_certificate_chain(
    receipt=receipt,
    certificate_chain=certificate_chain,
)
```

Expected output:

```json
{
  "verified": true,
  "chain_id": "chain-..."
}
```

## Evaluate A Policy

```python
from afritech.sdk import evaluate_policy

result = evaluate_policy(
    source="""
    policy production_release_trust
    require trust_score >= 75
    require federation_verified == true
    """,
    context={"trust_score": 91, "federation_verified": True},
)
```

Expected output:

```json
{
  "mode": "sdk_policy_evaluation",
  "allowed": true
}
```

## Submit A Trust Exchange Locally

```python
from afritech.sdk import submit_trust_exchange

exchange = submit_trust_exchange(
    issuer_org="org-alpha",
    subject_org="org-beta",
    receipt_hash="abc123",
    trust_score=91,
)
```

Expected output:

```json
{
  "mode": "cross_organization_trust_exchange",
  "verified": true
}
```

## Universal Artifact Validation

```python
from afritech.sdk import validate_artifact

result = validate_artifact({
    "artifact_type": "governance_receipt",
    "artifact": receipt,
})
```

Supported artifact types:

```text
governance_receipt
audit_package
portable_verification_package
certificate_chain
novascript_execution
```

## API Equivalent

```http
POST /v1/novascript/validate/artifact
```

Use the SDK for local/offline verification and the API for platform-integrated verification.
