# NovaTrust, NovaScript, NovaProgramming

## Core Platform Verified Implementation and 2026 Upgrade

## Status

- Implemented: deterministic backend services and FastAPI routes
- Wired: dashboard console surfaces and tests
- Pilot-ready: one deployable core payment-to-proof flow
- Pending for GA: live provider credentials, durable production database, PDF export, full observability

## NovaTrust

Mission: nothing is true unless provable.

Implemented files:

```text
afritech/core_platform/services.py
afritech/core_platform/persistence.py
afritech/api/core_platform_api.py
dashboard/src/App.jsx
```

Implemented behavior:

- Records deterministic proof packets.
- Hashes packet content into `event_hash`.
- Replays packets by recomputing the hash.
- Persists flow packets through the core platform store.
- Exposes public verification through `/trust/explorer/{receipt_or_trust_id}`.

API:

```text
POST /v1/core-platform/trust/replay
GET  /v1/core-platform/trust/explorer/{receipt_or_trust_id}
GET  /trust/explorer/{receipt_or_trust_id}
```

Trust Explorer UI zones:

```text
Timeline | Actor | Authority decision | Payment receipt | Replay result | AI explanation
```

## NovaScript

Mission: provide explainable intelligence without becoming authority.

Implemented behavior:

- Explains decisions using NovaPower and NovaTrust evidence.
- Returns risk level and recommended action.
- Binds explanations to trust and decision evidence references.

API:

```text
POST /v1/core-platform/ai/explain
```

Output includes:

```text
summary
risk_level
recommended_action
evidence_refs
```

## NovaProgramming

Mission: control how the system evolves safely.

Implemented behavior:

- Creates governed proposals.
- Sets lifecycle state from evidence-backed risk.
- Attaches validators: `test_suite`, `risk_scan`, `trust_replay`.
- Preserves NovaTrust and NovaPower evidence references.

API:

```text
POST /v1/core-platform/programming/proposals
```

## NovaPay Providers

Implemented provider adapters:

```text
afritech/core_platform/payments/providers.py
```

Providers:

- PayID: deterministic local/pilot provider.
- Stripe: live-capable adapter that can call the Stripe SDK when `STRIPE_API_KEY`
  and `STRIPE_LIVE_MODE=true` are configured.

Default pilot mode uses PayID so validation can run without external network calls.

Provider readiness endpoint:

```text
GET /v1/core-platform/payments/providers/status
```

## PostgreSQL Persistence

Implemented adapter:

```text
afritech/core_platform/persistence.py
```

Durable target table:

```text
novatech_core_trust_packets
```

Schema purpose:

- Store trust packet ID.
- Store payment receipt ID.
- Store organization ID.
- Store event type.
- Store canonical packet as JSONB.

Status endpoint:

```text
GET /v1/core-platform/persistence/status
```

Migration:

```text
afritech/core_platform/migrations/001_core_trust_packets.sql
```

ORM-style row mapper:

```text
afritech/core_platform/orm.py
```

## Pilot Flow

One deployable core flow is exposed:

```text
POST /v1/core-platform/pilot/flow
```

Flow:

```text
NovaID -> NovaPower -> NovaPay -> NovaTrust -> NovaScript -> NovaProgramming
```

The response includes:

- Authority decision
- Payment receipt
- Trust packet
- Replay-ready event hash
- AI explanation
- Programming proposal
- Public Trust Explorer link

For a real external pilot:

```text
POST /v1/core-platform/pilot/flow
{
  "provider": "stripe",
  "live_provider": true
}
```

The deployment environment must provide:

```text
STRIPE_API_KEY
STRIPE_LIVE_MODE=true
DATABASE_URL
```

Without those values, the code stays in deterministic pilot mode.

## PDF Audit Export

Implemented:

```text
afritech/core_platform/audit_export.py
```

Routes:

```text
GET /v1/core-platform/trust/explorer/{receipt_or_trust_id}/audit.pdf
GET /trust/explorer/{receipt_or_trust_id}/audit.pdf
```

The export is a compact PDF regulator packet containing actor, organization,
authority decision, payment receipt, trust ID, replay result, risk state, and
the public no-authority boundary.

Cryptographic signature:

```text
afritech/core_platform/signing.py
```

The PDF includes an Ed25519 signature summary. Signature endpoints:

```text
GET /v1/core-platform/trust/explorer/{receipt_or_trust_id}/signature
GET /trust/explorer/{receipt_or_trust_id}/signature
```

Production signing key:

```text
NOVATRUST_ED25519_PRIVATE_KEY_B64
NOVATRUST_SIGNING_KEY_ID
```

If no key is configured, the system uses a deterministic development key for
local validation only.

The PDF also embeds a deterministic verification QR-style matrix derived from
the Trust Explorer URL so regulators can visually bind the PDF to the public
verification route.

Key status and rotation:

```text
GET /v1/core-platform/signing/status
```

AWS production deployment wires:

```text
NOVATRUST_KMS_KEY_ID
NOVATRUST_KEY_ROTATION_ENABLED=true
```

## React Trust Explorer Frontend

Implemented:

```text
dashboard/src/TrustExplorer.jsx
```

The component renders:

- public explorer route
- API packet route
- verification timeline
- PDF export cue
- Ed25519 signature cue
- read-only boundary

When `receiptId` is supplied, it fetches live data from:

```text
/v1/core-platform/trust/explorer/{receiptId}
```

## Migration System

Implemented:

```text
afritech/core_platform/migration_system.py
scripts/novatech_core_apply_migrations.py
```

This is an Alembic-compatible linear SQL migration runner. It tracks applied
versions in:

```text
novatech_core_schema_migrations
```

Apply migrations:

```bash
DATABASE_URL=postgresql://... scripts/novatech_core_apply_migrations.py
```

## Enterprise Compliance Report

Implemented:

```text
afritech/core_platform/compliance_report.py
```

Routes:

```text
GET /v1/core-platform/trust/explorer/{receipt_or_trust_id}/compliance-report
GET /trust/explorer/{receipt_or_trust_id}/compliance-report
```

The report maps proof packets to ISO 27001, SOC 2, and regulator payment
traceability controls.

## Real-Time Auditor Dashboard

Implemented:

```text
afritech/core_platform/auditor_dashboard.py
dashboard/src/AuditorDashboard.jsx
```

Routes:

```text
POST /v1/core-platform/auditor/dashboard
GET  /trust/auditor/dashboard?ids={receipt_or_trust_ids}
```

The dashboard verifies multiple receipts, signatures, explorer links, PDF links,
and control coverage in one read-only view.

## Operator Scripts

```text
scripts/novatech_core_deploy_aws.sh
scripts/novatech_core_apply_migrations.py
scripts/novatech_core_live_pilot.py
```

The scripts are intentionally credential-driven and do not embed secrets.

External sharing bundle for each pilot:

```text
/trust/explorer/{trust_id}
/trust/explorer/{trust_id}/audit.pdf
/trust/explorer/{trust_id}/signature
/trust/explorer/{trust_id}/compliance-report
/trust/explorer/{trust_id}/anchor
/trust/explorer/{trust_id}/qr.png
/trust/explorer/{trust_id}/bundle.zip
```

Public local verification:

```bash
novatrust-verify --base-url http://16.176.215.89 --trust-id {trust_id}
```

The auditor ZIP includes:

```text
packet.json
signature.json
anchor.json
compliance-report.json
audit.pdf
verification-qr.png
README.txt
```

## Intranet and Extranet Wiring

Fixed and extended surfaces:

- Intranet exposes `/v1/core-platform/console`.
- Intranet exposes `/v1/core-platform/pilot/flow`.
- Extranet exposes `/trust/explorer/{receipt_or_trust_id}`.
- Platform route list now uses `/v1/novatech/extranet/status`.

## Validation

Focused validation commands:

```text
pytest -q afritech/tests/core_platform/test_core_platform_layers.py afritech/tests/api/test_core_platform_api.py afritech/tests/api/test_novatech_intranet_api.py dashboard/tests/test_operator_dashboard_surface.py
npm run build --prefix dashboard
git diff --check
```

AWS deployment assets:

```text
infra/aws/novatech-core-platform/
```

## Current Truth

NovaTech Core is now a deterministic, replayable, API-exposed trust platform
with public verification UI, provider-shaped payment integration, PostgreSQL
persistence adapter, and one pilot-ready core flow.

It is not full GA until live payment credentials, production database migration,
observability, and operational runbooks are active in a real deployment.
