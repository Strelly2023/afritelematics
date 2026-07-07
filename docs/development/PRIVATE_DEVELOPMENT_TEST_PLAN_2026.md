# Private Development Test Plan 2026

Status: LOCAL-ONLY DEVELOPER VALIDATION

## Purpose

This framework gives developers high confidence before controlled pilot testing.
It is strictly private-development only.

## What Private Development Means

- Local or development environments only
- No real payments
- No real charging
- No production credentials
- No external payout execution
- No real customer financial movement
- No public launch claims

## Allowed

- Mock users
- Mock cards
- Mock balances
- Simulated ledgers
- Sandbox identity verification
- Simulated receipts
- Local APK validation
- Local backend validation

## Blocked

- Live payment execution
- Real card storage
- Production API keys
- Production webhooks
- Public store launch claims
- Controlled pilot claims
- Customer-facing payout execution

## How To Run

```bash
python3 -m pytest -q tests/private_dev
python3 -m pytest -m "private_dev or local_only or simulated_payment or no_live_charge" tests/private_dev -q
```

Use the marker set to run only local validation surfaces.

## Simulated Payment Explanation

Simulated payments are ledger-only actions.
They update mock balances, create simulated receipts, and mark the response as simulated.
They must not call live providers or charge real instruments.

## APK Validation Explanation

APK validation checks that the release artifacts, checksum files, release manifests, and LAN download paths are present and consistent.

## Tab And Button Validation Explanation

The registry file lists required tabs and buttons for each app.
Tests compare the registry against the app source to confirm the surfaces exist and are wired to safe handlers.

## Private Development Versus Controlled Pilot

- Private development: local-only, simulated, developer validation
- Controlled pilot: approved real-device field testing with pilot governance, device registration, and evidence capture

## Checklist Before Controlled Pilot

- private development config is in place
- simulated payment guard passes
- app surfaces match the registry
- APK artifacts are present
- icon assets exist
- release guard rejects live-payment claims
- pilot runbook and RC certification gates exist

