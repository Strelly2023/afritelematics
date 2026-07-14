# NovaTech Federated API Platform

The NovaTech API platform publishes domain contracts instead of requiring
partners and internal teams to consume one large mixed OpenAPI surface.

## Products

- NovaRide: rides, drivers, passengers, fleet, dispatch, logistics, corporate, and transit.
- NovaPay: wallets, transfers, payment intents, settlement references, and ledger-owned operations.
- NovaID: identity, devices, credentials, consent, and trust posture.
- NovaTrust: replay, evidence, signatures, receipts, and verification.
- NovaProgramming: workflows, agents, artifacts, and assurance.
- Operations: health, readiness, metrics, and dashboards.
- Public Verification: public proofs and trust badges.
- Partner: onboarding, webhooks, API keys, and certification.

## Contract Endpoints

- `GET /v1/platform/api-catalog`
- `GET /v1/platform/api-catalog/{domain}`
- `GET /v1/platform/api-catalog/{domain}/versions`
- `GET /v1/platform/api-catalog/{domain}/publication`
- `GET /openapi/{domain}.json`
- `GET /v1/platform/releases`
- `GET /v1/platform/compatibility`
- `GET /v1/platform/deprecations`
- `GET /v1/platform/migrations`

Each domain OpenAPI document includes `x-novatech-*` governance extensions for
domain, maturity, audience, authority, evidence, risk, idempotency, and
deprecation migration metadata.

## Partner Certification

Partner certification follows:

`Registered -> Sandbox Enabled -> Contract Compatible -> Security Verified -> Webhook Verified -> Load Tested -> Certified -> Production Enabled`

The platform exposes:

- `GET /v1/partner/certification/status`
- `POST /v1/partner/certification/run`
- `GET /v1/partner/certification/evidence`

Production enablement remains separately governed.
