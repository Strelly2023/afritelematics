# AfriTech Live System Integrity Demo

Status: PARTNER LIVE SYSTEM INTEGRITY DEMO

Classification: PARTNER-FACING EXTERNAL VERIFICATION RUNBOOK

Purpose: provide a partner-safe walkthrough that demonstrates startup-safety,
architecture proof, public verification, and anchor-backed integrity without
granting any execution or mutation authority.

## Public Demo Surfaces

- `GET /public/architecture/health`
- `GET /public/architecture/proof`
- `GET /public/registry`
- `GET /public/verify/{anchor_id}`
- `GET /public/demo/system-integrity`

## Operator Correlation Surface

- `GET /v1/system/integrity/dashboard`

This dashboard is replay-backed, audit-aware, and read-only. It exists to help
operators and partner observers correlate:

- runtime boundary status
- anchored architecture artifacts
- public verification packet state
- audit readiness

## Walkthrough

1. Open `/public/architecture/health`
   Explain that the FastAPI startup path is verified and externally readable.
2. Open `/public/architecture/proof`
   Show the boundary contract hash, runtime-boundary scan hash, full
   architecture graph hash, and the cryptographic anchor commitment.
3. Open `/public/verify/{anchor_id}`
   Show that the public surface resolves a bounded verification packet and a
   registry entry only.
4. Open `/public/demo/system-integrity`
   Walk the partner through the exact sequence and claims without improvising
   or widening authority.
5. Open `/v1/system/integrity/dashboard`
   Show the same proof id, anchor id, publication id, and audit readiness from
   the operator view.

## What Partners Should Hear

- The architecture proof is externally inspectable.
- The anchor proves export integrity only.
- Replay and governed execution remain the authority.
- Public verification is read-only and bounded.
- The same evidence appears in public proof, operator dashboard, and registry
  views.

## Non-Claims

- This demo does not grant partner write access.
- This demo does not replace replay with anchoring.
- This demo does not claim that dashboards define truth.
