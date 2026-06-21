# NovaScript Ecosystem Map

NovaScript is a standards-backed platform ecosystem, not only a codebase.

```text
NovaScript
|
+-- SDK
+-- API
+-- Policy Registry
+-- Certificate Authority
+-- Assurance Engine
+-- Federation
+-- Public Trust Portal
+-- Trust Network
```

## SDK

The SDK provides local/offline validation helpers:

```text
verify_receipt()
verify_audit_package()
validate_artifact()
evaluate_policy()
validate_certificate_chain()
submit_trust_exchange()
```

## API

The API exposes platform validation and trust operations:

```text
POST /v1/novascript/generate
POST /v1/novascript/validate/artifact
POST /v1/novascript/audit/verify
POST /v1/novascript/federation/trust-exchange
GET  /v1/novascript/trust/graph
```

## Policy Registry

The registry stores versioned policy-as-code and links decisions to policy versions and hashes.

## Certificate Authority

NovaTrust CA issues root, organization, and receipt certificate chains for provenance verification.

## Assurance Engine

The assurance layer tracks trust, risk, policy, architecture, compliance, and evidence drift.

## Federation

Federation records cross-organization trust exchanges and exposes them through the trust graph.

## Public Trust Portal

The public portal exposes read-only verification endpoints for receipts, certificates, assurance reports, and portable packages.

## Trust Network

The trust network connects organizations, validators, auditors, partners, and public verification surfaces.

## Ecosystem Boundary

Each ecosystem component contributes evidence, validation, or presentation. None may override proof truth or independently claim production authority.
