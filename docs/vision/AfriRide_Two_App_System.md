# AfriRide Two-App System

STATUS: FUTURE IMPLEMENTATION SURFACE

This document describes a future AfriRide passenger and driver app interface layer.

It is not part of `afritech.demo.proof`, does not define system correctness, and must not introduce new proof claims.

System correctness remains defined exclusively by:

```bash
python3 -m afritech.demo.proof
```

## Boundary

```text
afritech = core truth engine
afriride_system = interaction layer
```

Apps produce commands. They do not define system behavior.

## Target Structure

```text
afriride_system/
  clients/
    passenger_app/
    driver_app/
  backend/
    api_gateway/
    command_api/
    query_api/
  integration/
    websocket_gateway/
    notification_adapter/
    map_adapter/
```

## Passenger App

Core screens:

- home screen with map, current location, destination input, and request ride action
- ride request flow with destination, fare estimate, and confirmation
- matching screen with driver search, assignment, and tracking
- trip screen with driver info, route tracking, and ETA
- payment screen for cash, mobile money, and card
- rating screen for driver rating and feedback

## Driver App

Core screens:

- dashboard with online/offline status and earnings summary
- incoming request screen with accept and reject actions
- navigation to pickup and destination
- trip lifecycle actions for arrive, start trip, and complete trip
- earnings and trip history

## Command Model

The interface layer maps user actions to AfriRide commands:

```text
request_ride
assign_driver
accept_driver
start_trip
complete_trip
cancel_trip
```

These commands must be dispatched into the AfriTech runtime boundary. API handlers must not contain business logic.

## API Contract

Passenger API:

```text
POST /passenger/request-ride
GET  /passenger/ride-status/{ride_id}
POST /passenger/cancel-ride
POST /passenger/rate-driver
```

Driver API:

```text
POST /driver/status
GET  /driver/requests
POST /driver/accept-ride
POST /driver/start-trip
POST /driver/complete-trip
```

## Real-Time Layer

WebSocket channels:

```text
ride_updates:{ride_id}
driver_updates:{driver_id}
```

Events:

- driver_assigned
- driver_arrived
- trip_started
- trip_completed

## Flow

```text
Passenger -> request_ride
        -> command handler
        -> AfriTech runtime
        -> deterministic execution and replay
        -> dispatch outcome
        -> event emitted
        -> apps updated
```

All state changes remain inside the AfriTech runtime boundary.

## Testing Scope

Future app simulation may test:

- passenger requests ride
- driver accepts ride
- trip starts
- trip completes
- driver disconnects
- network retry occurs

These tests are interface validation only. They do not expand the proof surface.

## Non-Claims

This document does not claim:

- passenger app implementation exists
- driver app implementation exists
- production readiness
- mobile deployment readiness
- new proof claims beyond the current AfriRide continuity proof

## MVP Plan

See [AfriRide GA Elite MVP](AfriRide_GA_Elite_MVP.md).
