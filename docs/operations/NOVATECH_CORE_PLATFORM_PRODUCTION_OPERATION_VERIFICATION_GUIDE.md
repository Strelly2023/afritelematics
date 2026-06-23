# NovaTech Core Platform Production Operation and Verification Guide

## Status Boundary

This guide describes the production operation path for the NovaTech core
platform services implemented in this repository.

The following container state was reported by the operator and should be
verified on the host before running a live pilot:

```text
production-afritech-api       healthy
production-afritech-dashboard running
production-nginx              running
```

## Runtime Health Checks

Run from the production host:

```bash
docker ps
curl http://localhost:8000/health
curl http://localhost:8000/v1/core-platform/payments/providers/status
curl http://localhost:8000/v1/core-platform/signing/status
```

The provider status must report:

```json
{
  "ready_for_real_charge": true
}
```

before any live Stripe pilot is attempted.

## NovaPay Live Mode Gate

A real Stripe payment can occur only when every condition is true:

```text
STRIPE_API_KEY is configured
STRIPE_LIVE_MODE=true
request payload sets live_provider=true
NovaPower returns ALLOW
```

Runtime environment:

```bash
STRIPE_API_KEY=sk_live_...
STRIPE_LIVE_MODE=true
```

Pilot payload:

```json
{
  "provider": "stripe",
  "live_provider": true
}
```

## PostgreSQL Persistence

Current safe local default:

```text
InMemoryCorePlatformStore
```

Production persistence requires:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/novatech
```

Apply migrations:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/novatech \
  scripts/novatech_core_apply_migrations.py
```

The migration creates:

```text
novatech_core_trust_packets
novatech_core_schema_migrations
```

## Signing and Key Rotation

Local signing uses Ed25519. Production deployments should configure KMS metadata
and a managed signing key:

```bash
NOVATRUST_ED25519_PRIVATE_KEY_B64=<base64 raw ed25519 private key>
NOVATRUST_SIGNING_KEY_ID=novatrust-prod-001
NOVATRUST_KMS_KEY_ID=<aws_kms_key_id>
NOVATRUST_KEY_ROTATION_ENABLED=true
NOVATRUST_KEY_ROTATION_DAYS=90
```

Check status:

```bash
curl http://localhost:8000/v1/core-platform/signing/status
```

## Live Pilot Execution

Required variables:

```bash
export NOVATECH_API_BASE_URL=http://localhost:8000
export NOVATECH_BEARER_TOKEN=<operator-or-verifier-token>
export NOVATECH_PILOT_AMOUNT=10.00
export NOVATECH_PILOT_CURRENCY=AUD
export NOVATECH_PILOT_DESTINATION=external-pilot
```

Run:

```bash
scripts/novatech_core_live_pilot.py
```

Expected output includes:

```text
Explorer: http://localhost:8000/trust/explorer/{trust_id}
PDF: http://localhost:8000/trust/explorer/{trust_id}/audit.pdf
```

## External Verification and Distribution Layer

This is the final externally consumable trust interface for NovaTech. It turns
one internal execution into portable evidence that can be inspected by an
external user, auditor, regulator, or investor without granting execution
authority.

Public sandbox entry point:

```text
http://16.176.215.89/trust/sandbox/demo
```

The sandbox returns read-only links for `sandbox-demo` and exists for public
demo, SDK validation, auditor onboarding, and integration testing.

Verification artifacts are designed around this contract:

```text
Explorer = human verification
Signature = cryptographic proof
Compliance = audit mapping
Anchor = deterministic cryptographic binding
QR-style PNG verification image = visual document linkage
ZIP = complete portable bundle
CLI = independent local verification
```

The current anchor is a deterministic NovaTrust binding layer. It binds the
canonical packet hash and signature hash into stable metadata. This is NOT yet
an external notarization system. It is ready to be extended by a live blockchain
or RFC3161 timestamp authority publisher. The current QR surface is a QR-style
PNG verification image generated without external dependencies, not a
standards-compliant QR code; the authoritative verification mechanism remains
the explorer URL and Ed25519 signature.

## External Sharing Bundle

After one successful pilot, share these artifacts with the external user,
auditor, or regulator:

```text
http://16.176.215.89/trust/sandbox/demo
http://16.176.215.89/trust/explorer/{trust_id}
http://16.176.215.89/trust/explorer/{trust_id}/audit.pdf
http://16.176.215.89/trust/explorer/{trust_id}/signature
http://16.176.215.89/trust/explorer/{trust_id}/compliance-report
http://16.176.215.89/trust/explorer/{trust_id}/anchor
http://16.176.215.89/trust/explorer/{trust_id}/qr.png
http://16.176.215.89/trust/explorer/{trust_id}/bundle.zip
```

Artifact responsibilities:

```text
/trust/explorer/{trust_id}
  Human-readable execution proof with identity, authority, payment, and replay.

/trust/explorer/{trust_id}/audit.pdf
  Portable audit artifact with signature metadata, payload hash, verification
  URL, and embedded visual verification matrix.

/trust/explorer/{trust_id}/signature
  Ed25519 signature payload for local machine verification.

/trust/explorer/{trust_id}/compliance-report
  ISO/SOC2/payment traceability control mapping linked to the packet.

/trust/explorer/{trust_id}/anchor
  Deterministic chain-of-trust metadata binding packet hash and signature hash.

/trust/explorer/{trust_id}/anchor/blockchain
  Optional blockchain anchoring adapter status. Disabled unless explicitly
  configured with an external publisher.

/trust/explorer/{trust_id}/qr.png
  QR-style PNG verification image for printed audit packs and mobile handoff.

/trust/explorer/{trust_id}/bundle.zip
  Complete offline auditor package.
```

For multiple receipts:

```text
http://16.176.215.89/trust/auditor/dashboard?ids={trust_id_1},{trust_id_2}
```

Local verification CLI:

```bash
novatrust-verify \
  --base-url http://16.176.215.89 \
  --trust-id {trust_id} \
  --write-dir ./novatrust-verification-{trust_id}
```

The CLI downloads `packet.json`, `signature.json`, and
`compliance-report.json`, validates the payload hash, verifies the Ed25519
signature, and writes `verification-result.json`.

Auditor ZIP contents:

```text
packet.json
signature.json
anchor.json
compliance-report.json
audit.pdf
verification-qr.png
README.txt
```

## Public Verification Guarantees

Public users can:

```text
view proof
download signed PDF
verify signature metadata
inspect compliance mapping
compare multiple receipts
download auditor ZIP bundle
verify chain anchor metadata
```

Public users cannot:

```text
execute payments
change proof packets
change authority decisions
modify compliance reports
```

## AWS Production Architecture

Infrastructure code:

```text
infra/aws/novatech-core-platform/
```

Deploy:

```bash
scripts/novatech_core_deploy_aws.sh
```

The stack provisions:

```text
ECS Fargate API
Application Load Balancer
RDS PostgreSQL
CloudWatch logs
Secrets Manager Stripe key reference
KMS key for NovaTrust signing metadata and rotation readiness
```

## GA Activation Checklist

```text
1. Verify containers are healthy.
2. Configure DATABASE_URL.
3. Apply migrations.
4. Configure STRIPE_API_KEY and STRIPE_LIVE_MODE=true.
5. Configure NOVATRUST signing variables.
6. Verify provider status.
7. Verify signing status.
8. Execute one controlled live pilot.
9. Open Trust Explorer.
10. Download PDF.
11. Verify signature.
12. Review compliance report.
13. Share external verification bundle.
```

## Reality Boundary

This repository contains the deploy-ready code, infrastructure, scripts, and
verification routes. Actual live payment execution and managed cloud deployment
require production credentials, production environment variables, and explicit
operator approval.
