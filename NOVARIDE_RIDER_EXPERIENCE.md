# NovaRide Rider Experience

Repository: /Users/ostrinov/afritelematics
Branch: feature/novacodepro-unified-platform
Commit: 0ebce8bc57f568033f48035ac16a74562dff17e4
Timestamp: 2026-07-20T00:50:09.269547+00:00

The rider app currently supports:

- login and session restore
- booking flow with pickup, destination, fare, and ride type selection
- driver assignment and live tracking
- waiting and no-show handling
- payment, receipt, evidence, and replay views
- support, wallet, profile, trust, and safety surfaces

Validation:

- `pytest -q rider_app/tests`
- `npm run typecheck --prefix rider_app`

Status: API-connected and locally verified.
