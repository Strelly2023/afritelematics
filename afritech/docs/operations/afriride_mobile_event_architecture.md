# AfriRide Mobile Event Architecture

STATUS: FUTURE PILOT IMPLEMENTATION SURFACE
CLASSIFICATION: MOBILE EVENT-PRODUCER ARCHITECTURE

## Boundary

Mobile apps are not runtime truth, replay authority, proof authority, or direct
state mutation surfaces.

Mobile apps are deterministic event producers feeding the constitutional
pipeline.

The current repository contains React Native Expo stubs under
`afriride_system/mobile`. For city pilot implementation, Flutter is the
recommended target architecture because it gives stronger control over offline
persistence, platform timing behavior, and structured event pipelines.

This document does not claim that the Flutter apps are implemented, deployed, or
approved for app store release.

## Architecture

```text
DRIVER / RIDER APP
-> LOCAL EVENT BUFFER
-> EDGE-COMPATIBLE EVENT FORMAT
-> SYNC ENGINE
-> EDGE ADAPTER
-> NORMALIZATION
-> ADMISSION
-> EXECUTION
-> WITNESS
-> REPLAY
```

## Target Folder Structure

```text
mobile/
  core/
    event/
    sync/
    storage/
    network/
    security/
    replay_safe_clock/
  driver/
    screens/
    controllers/
    events/
  rider/
    screens/
    controllers/
    events/
```

## Event-First Rule

All app actions produce events.

Allowed:

```text
UI action -> event -> local buffer -> sync -> edge adapter
```

Forbidden:

```text
UI action -> direct API mutation
mobile state -> runtime truth
GPS reading -> core mutation
payment screen -> settlement truth
```

## Canonical Mobile Event

```yaml
event:
  event_id: evt_123
  device_id: driver_45
  event_type: DRIVER_ACCEPTED_RIDE
  logical_timestamp: 17
  payload:
    ride_id: ride_88
```

Client wall-clock time is observational only. The app emits a logical timestamp
from a monotonic local counter; server-side normalization supplies admission time
authority later.

## Core Modules

### Event Store

Required behavior:

```text
append-only pending event storage
FIFO retrieval by logical timestamp
crash recovery
mark-sent only after acknowledged sync
no event loss on offline restart
```

### Replay-Safe Clock

Required behavior:

```text
monotonic local counter
no wall-clock authority
counter persisted across app restart
```

### Sync Engine

Required behavior:

```text
same pending events -> same send order
no parallel mutation sends
idempotent retry by event_id
duplicate sends permitted only as duplicate observations
server-side normalization remains authoritative
```

### Network Client

Required behavior:

```text
POST /events with event and signature
one mutation event in flight per device stream
retry with same event_id
no business logic in network client
```

### Client Security

Required behavior:

```text
sign canonical event content
include event_id and logical_timestamp
never sign runtime witness claims
never generate replay authority fields
```

## Driver Event Set

```text
DRIVER_LOCATION_RECORDED
DRIVER_AVAILABILITY_CHANGED
DRIVER_ACCEPTED_RIDE
DRIVER_REJECTED_RIDE
DRIVER_ARRIVED_PICKUP
TRIP_STARTED
TRIP_COMPLETED
```

GPS handling:

```text
raw GPS
-> batched local observation events
-> synced as mobile observations
-> normalized server-side
```

## Rider Event Set

```text
RIDER_REQUESTED_RIDE
RIDER_CANCELLED_RIDE
RIDER_CONFIRMED_PICKUP
RIDER_PAYMENT_TRIGGERED
RIDER_RATED_DRIVER
```

Payment handling:

```text
payment UI action
-> payment observation event
-> edge normalization
-> external settlement evidence recorded separately
```

## Pilot Test Obligations

```yaml
mobile_tests:
  offline_mode:
    verifies:
      - events collected without network
      - sync preserves deterministic order
      - replay after sync converges
  duplicate_sends:
    verifies:
      - same event_id may be resent
      - normalization/admission remains stable
      - no duplicate mutation authority
  reordering:
    verifies:
      - out-of-order sync does not become execution order authority
      - normalized trace remains deterministic
  crash_recovery:
    verifies:
      - pending event buffer survives restart
      - logical clock does not reset
  tamper_attempt:
    verifies:
      - modified event payload fails integrity checks
      - forbidden replay or witness fields are rejected
```

## Non-Claims

This architecture does not claim:

```text
Flutter app implementation exists
mobile deployment readiness
app store approval
production mobile reliability guarantees
payment provider integration completed
mobile events define execution truth
```

## Safe Final Classification

AfriRide mobile apps are deterministic event emitters with offline-first
behavior, replay-safe ordering, secure event signatures, and synchronization
discipline.

They feed the constitutional system; they do not replace it.
