# Internal QA Test Plan 2026

## Purpose
Internal QA validates NovaTech after private development and before controlled pilot approval.

## Boundary Rules
- Internal staff and testers only
- QA builds only
- No public users
- No live commercial payment by default
- Simulated payments are allowed
- Sandbox providers are allowed
- Real payments are blocked unless `qa_live_payment_approved` is explicitly granted
- NovaID authenticates identity
- NovaPay executes payments
- NovaRide handles mobility
- NovaTrust records evidence
- NovaAI remains advisory only

## Coverage
- NovaRide rider, driver, and operator surfaces
- NovaPay consumer, agent, merchant, and business surfaces
- NovaID personal, business, employee, partner, and inspector surfaces
- APK release artifacts and checksums
- API contracts and protected routes
- Button registry and route safety
- Release-guard assertions

## Execution
Run the internal QA test suite from the repository root:

```bash
python -m pytest tests/internal_qa -q
python -m pytest -m "internal_qa or qa_smoke or qa_mobile or qa_api or qa_release_guard or simulated_payment or no_live_charge" tests/internal_qa -q
```

## Pre-Controlled-Pilot Checklist
- Internal QA config present
- Simulated payment paths pass
- Sandbox identity paths pass
- APK artifacts and checksums verify
- Icons and release manifests verify
- API contracts are present or mocked
- Regression matrix references previous suites
- No production or public-launch claims
