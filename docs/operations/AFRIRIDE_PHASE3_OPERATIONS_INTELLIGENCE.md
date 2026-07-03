# AfriRide Phase 3 operations and intelligence

Phase 3 adds explainable weighted dispatch without changing ride authority or
the `afriride.mobility.v1` transport. The optimization contract is
`afriride.dispatch.v1`.

## Weighted dispatch

The default policy scores distance, traffic, rating, vehicle match, acceptance
rate, trust, battery, ETA and surge readiness. Weights sum to one and every
candidate response includes normalized factors, weighted contributions,
eligibility gates and exclusions. Stable tie-breaking uses score, ETA and
driver ID, making decisions deterministic and replayable.

Hard gates exclude offline or untrusted devices, trust below 60, battery below
10%, open safety incidents and fraud risk above 0.70. These gates cannot be
overridden by a high proximity score.

`POST /v1/operations/dispatch/optimize` is advisory. Automatic execution is
allowed only when the winning score is at least 0.72 and its margin is at least
0.08. `POST /v1/operations/dispatch/execute` then calls the existing
authoritative dispatcher and supports idempotency keys. WebSockets remain
observational.

## Operations surfaces

`GET /v1/operations/dashboard` projects:

- dispatch decision and review counts;
- the latest complete scoring explanation;
- fleet rating, acceptance, trust, ETA and availability aggregates;
- fraud, integrity, battery and safety alerts;
- bounded automation eligibility.

Phase 3 publishes `DISPATCH_OPTIMIZED`, `FLEET_ANALYTICS_UPDATED` and
`OPERATIONAL_ALERT` through the existing Redis-backed mobility stream.

## Governance and alert runbook

Weights and gates are versioned policy, not an opaque model. Changes require
offline evaluation against completion time, cancellation, fairness, safety and
driver-distribution metrics before rollout. Never train directly on protected
attributes or use them as dispatch factors.

Critical integrity, fraud or safety alerts exclude a driver and require an
operator investigation. Low battery is warning-only until it crosses the hard
gate. During analytics failure, disable automatic execution and retain the
existing dispatcher/manual assignment path.
