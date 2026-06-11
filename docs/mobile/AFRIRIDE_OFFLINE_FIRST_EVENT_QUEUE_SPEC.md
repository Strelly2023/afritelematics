# AfriRide Offline-First Event Queue Specification

Status: OFFLINE-FIRST EVENT QUEUE SPECIFICATION
Classification: MOBILE_RESILIENCE_EXECUTION_SURFACE

Purpose: define the offline-first event queue behavior required for real device
deployments with weak or intermittent networks.

This specification is a mobile resilience surface.
It is not proof that every offline scenario has already been field-validated.

## Source Alignment

This spec is grounded in the existing mobile and pilot surfaces:

- Expo mobile client request and idempotency behavior in `afriride_system/mobile/shared/apiClient.js`
- Flutter pilot `event_store.dart`
- Flutter pilot `logical_clock.dart`

## Offline-First Goal

When connectivity degrades, the mobile client must:

- preserve event order
- preserve event identity
- preserve logical progression
- avoid client-side authority claims

## Queue Rules

### Rule 1. Queue Before Lossy Retry

If a write action cannot be confirmed, the client must preserve the request
intent in a queue before repeated retries continue.

### Rule 2. Stable Event Identity

Queued operations must retain:

- event id
- logical clock or deterministic order marker
- actor identity
- original payload
- timestamp envelope

### Rule 3. Deterministic Flush Order

Queued items must flush in:

- logical clock order first
- event id order second

This matches the existing pilot event-store sorting discipline.

### Rule 4. Idempotent Replay Safety

Write actions must preserve the same idempotency key across retry attempts for
the same queued intent.

### Rule 5. No Local Truth Override

Offline mode may present pending state.
Offline mode may not declare ride truth, receipt truth, replay truth, or
verification truth locally.

## Required Failure Scenarios

- no network on ride request
- delayed confirmation on driver accept
- reconnect after app backgrounding
- duplicate retry after timeout
- queue flush after partial success

## Required Evidence

- preserved idempotency key reuse
- preserved event ordering
- no duplicate committed mutation from the same queued intent
- replay and evidence remain authoritative after reconnect

## Mandatory Boundary

This spec permits only this bounded claim:

```text
AfriRide has a clear offline-first event queue model for weak-network mobile
deployments
```

