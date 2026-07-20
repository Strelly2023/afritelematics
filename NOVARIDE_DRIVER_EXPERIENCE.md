# NovaRide Driver Experience

Repository: /Users/ostrinov/afritelematics
Branch: feature/novacodepro-unified-platform
Commit: 0ebce8bc57f568033f48035ac16a74562dff17e4
Timestamp: 2026-07-20T00:50:09.269547+00:00

The driver app currently supports:

- login and session restore
- readiness checks and shift gating
- availability, request queue, trip lifecycle, and earnings flows
- vehicle, diagnostics, replay history, profile, notifications, and operator dashboard views
- pilot evidence and offline queueing for availability and trip commands

Validation:

- `pytest -q driver_app/tests`
- `npm run typecheck --prefix driver_app`

Status: API-connected and locally verified.
