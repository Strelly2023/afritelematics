# Internal QA Test Framework

## What Internal QA Means
Internal QA is the validation layer between private development and controlled pilot. It is restricted to internal staff and tester accounts and uses QA-only builds.

## Allowed
- Sandbox identity flows
- Simulated payment flows
- QA-ledger cash flows
- Mocked or sandbox API providers
- Local APK validation
- Internal device and server checks

## Blocked
- Production credentials
- Live charging
- External payouts
- Public launch claims
- Production-ready claims
- Controlled pilot approval by default

## How To Run
```bash
python -m pytest tests/internal_qa -q
python -m pytest -m "internal_qa or qa_smoke or qa_mobile or qa_api or qa_release_guard or simulated_payment or no_live_charge" tests/internal_qa -q
```

## Policies
- Payment state must remain simulated unless a controlled-pilot procedure explicitly enables a live path.
- Identity flows must remain sandboxed.
- APK validation must ensure checksums, manifests, icons, and version fields exist.
- Button validation must ensure tabs and actions are mapped to implemented or safely mocked handlers.

## Before Controlled Pilot
- Internal QA suite passes
- Regression matrix passes
- No live-payment path is enabled
- No production credential is required
- Release checklist is complete
