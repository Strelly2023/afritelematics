# NovaScript Trust Specification v1

Status: PUBLIC REFERENCE SPECIFICATION

Classification: VERIFIABLE AI-GENERATED SOFTWARE TRUST STANDARD

NovaScript Trust Specification v1, abbreviated NTS v1, defines a public reference model for verifiable AI-generated software systems.

## Positioning

```text
NovaScript is the standard for verifiable AI-generated software systems.
```

NTS v1 is open for implementation by external tools, platforms, auditors, and regulated organizations. It defines artifact shapes, validation rules, lifecycle expectations, and interoperability boundaries. It does not grant production authority, legal certification, or standards body ratification by itself.

## Governance Artifacts

NTS v1 defines these core artifacts:

```text
policy_decision
certificate_chain
governance_receipt
assurance_report
portable_verification_package
trust_exchange
production_evidence
```

## Trust Contract

Required trust fields:

```text
trust_score: integer 0..100
risk_score: integer 0..100
assurance_status: "assured" | "review"
policy_required: true
receipt_required: true
certificate_required: true
```

## Canonical Execution Artifact

```json
{
  "artifact_type": "novascript_execution",
  "policy_decision_id": "policy-decision-...",
  "certificate_chain_id": "chain-...",
  "assurance_status": "assured"
}
```

## Governance Receipt

Required fields:

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

Validation rule:

```text
signature == sha256(receipt_id:prompt_hash:output_hash:trust_score:status:sequence)
```

## Certificate Chain

A valid NovaTrust chain includes:

```text
root_certificate
organization_certificate
receipt_certificate
federation_consensus
chain_hash
```

Validation rules:

```text
root_certificate.certificate_id == novatrust-root-v1
organization_certificate.issuer == root_certificate.certificate_id
receipt_certificate.subject == governance_receipt.receipt_id
federation_consensus.verified == true
chain_hash present
```

## Policy Decision

A policy decision must link to:

```text
policy_id
policy_version
policy_hash
allowed
decision_id
```

The decision is valid only for the policy version and hash used during evaluation.

## Assurance Report

An assurance report must include:

```text
report_id
organization_id
project_id
assurance_status
certificate_chain_hash
policy_decision_id
report_hash
```

## Portable Verification Package

Portable packages must include deterministic file hashes:

```text
receipt.json
certificate.json
assurance.json
proof.json
explanation.json
verification_manifest.json
```

Manifest requirements:

```text
offline_verification == true
requires_novascript_runtime == false
manifest_hash present
```

## Verification Rules

An NTS-compliant validation must check:

```text
receipt valid
certificate chain valid
policy decision allowed
federation consensus true
assurance status acceptable
portable manifest valid when supplied
```

## Lifecycle

```text
create
-> evaluate policy
-> issue receipt
-> issue certificate chain
-> assess assurance
-> persist canonical record
-> package verification artifacts
-> publish audit or public verification surface
```

## Compliance Mapping

NTS v1 maps to compliance concepts as follows:

```text
policy_decision        -> governance control
governance_receipt     -> decision evidence
certificate_chain      -> provenance control
assurance_report       -> continuous monitoring evidence
production_evidence    -> operational validation evidence
portable_package       -> independent verification bundle
trust_exchange         -> cross-organization validation record
```

## Universal API

NTS-compatible systems should expose:

```http
POST /v1/novascript/validate/artifact
```

Supported artifact types:

```text
governance_receipt
audit_package
portable_verification_package
certificate_chain
novascript_execution
```

## SDK Functions

Reference SDK functions:

```text
verify_receipt()
verify_audit_package()
evaluate_policy()
validate_certificate_chain()
submit_trust_exchange()
validate_artifact()
```

## NTS Examples

These examples are illustrative shapes for implementers. Real signatures and hashes must be computed from canonical payloads.

## Example Governance Receipt

```json
{
  "receipt_id": "rcpt-001",
  "organization_id": "org-alpha",
  "project_id": "project-payments",
  "prompt_hash": "sha256-prompt",
  "output_hash": "sha256-output",
  "trust_score": 92,
  "status": "approved",
  "sequence": 1,
  "signature": "sha256-signature"
}
```

## Example Certificate Chain

```json
{
  "chain_id": "chain-001",
  "organization_id": "org-alpha",
  "project_id": "project-payments",
  "root_certificate": {
    "certificate_id": "novatrust-root-v1",
    "subject": "NovaTrust Root",
    "issuer": "NovaTrust Root",
    "scope": "engineering_trust_verification"
  },
  "organization_certificate": {
    "certificate_id": "novatrust-org-org-alpha",
    "subject": "org-alpha",
    "issuer": "novatrust-root-v1",
    "scope": "organization_trust_authority"
  },
  "receipt_certificate": {
    "certificate_id": "novatrust-receipt-rcpt-001",
    "subject": "rcpt-001",
    "issuer": "novatrust-org-org-alpha",
    "scope": "governance_receipt"
  },
  "federation_consensus": {
    "federation_id": "fed-001",
    "verified": true,
    "payload_hash": "sha256-payload"
  },
  "chain_hash": "sha256-chain"
}
```

## Example Assurance Report

```json
{
  "mode": "formal_assurance_reporting",
  "report_id": "assurance-report-001",
  "organization_id": "org-alpha",
  "project_id": "project-payments",
  "assurance_status": "assured",
  "certificate_chain_hash": "sha256-chain",
  "policy_decision_id": "policy-decision-001",
  "report_hash": "sha256-report"
}
```

## Example Portable Package

```json
{
  "mode": "portable_verification_package",
  "package_id": "verifypkg-001",
  "receipt_id": "rcpt-001",
  "files": {
    "receipt.json": "sha256-receipt",
    "certificate.json": "sha256-chain",
    "assurance.json": "sha256-report",
    "proof.json": "sha256-proof",
    "explanation.json": "sha256-explanation"
  },
  "verification_manifest": {
    "manifest_id": "manifest-001",
    "manifest_hash": "sha256-manifest",
    "offline_verification": true,
    "requires_novascript_runtime": false
  }
}
```

## Example Trust Exchange

```json
{
  "mode": "cross_organization_trust_exchange",
  "exchange_id": "trustx-001",
  "issuer_org": "org-alpha",
  "subject_org": "org-beta",
  "receipt_hash": "sha256-receipt-output",
  "trust_score": 92,
  "verified": true,
  "exchange_hash": "sha256-exchange"
}
```

## Example Universal Validation Request

```json
{
  "artifact_type": "governance_receipt",
  "artifact": {
    "receipt_id": "rcpt-001",
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

## Non-Claims

NTS v1 does not claim:

```text
formal standards body approval
legal audit replacement
production authorization
model truth
currency or transferable economic value
runtime mutation authority
```
