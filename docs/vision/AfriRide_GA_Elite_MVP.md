# AfriRide GA Elite MVP

STATUS: FUTURE IMPLEMENTATION

This document describes a future Phase 1 mobile-ready AfriRide implementation plan.

It is not part of `afritech.demo.proof`, does not define system correctness, and must not introduce new proof claims.

System correctness remains defined exclusively by:

```bash
python3 -m afritech.demo.proof
```

## Phase 1 Objective

Build a working AfriRide interaction loop:

```text
Passenger requests ride
-> driver accepts
-> trip starts
-> trip completes
-> state remains replay-verifiable
```

## Success Conditions

- app flow works end to end
- user actions map to AfriRide commands
- API layer remains adapter-only
- no proof output changes
- no new claims are introduced

## System Layers

Core:

```text
afritech/
ecosystems/afriride/
```

The core is already proven for the current bounded continuity surface and must not be changed for MVP interface work.

API layer:

```text
afriride_api/
  passenger_routes.py
  driver_routes.py
  command_dispatcher_adapter.py
```

Rule:

```text
API = adapter only
No business logic in routes
```

Real-time layer:

```text
realtime/
  websocket_server.py
  event_bridge.py
```

Client apps:

```text
passenger_app/
driver_app/
```

Recommended MVP stack:

- FastAPI or Django REST for backend
- WebSocket or Firebase for real-time updates
- React Native Expo for mobile apps

## Passenger App MVP

Screens:

- home screen with map placeholder, pickup, destination, and request ride action
- matching screen showing driver search and driver found state
- ride tracking screen with driver info and status
- completion screen with trip completed state and optional simple rating

Excluded:

- payments
- promotions
- ride history
- advanced UI

## Driver App MVP

Screens:

- dashboard with online and offline toggle
- incoming request with accept and reject actions
- trip flow with navigate to pickup, start trip, and complete trip
- summary screen with completed trip and static earnings

Excluded:

- analytics
- advanced dashboards
- driver matching AI

## Command Flow

Passenger:

```text
POST /passenger/request-ride
-> request_ride command
```

Driver:

```text
POST /driver/accept
-> accept_driver command
```

Trip:

```text
POST /driver/start
-> start_trip command

POST /driver/complete
-> complete_trip command
```

All commands must be dispatched into the AfriTech runtime boundary.

## API Contract

Passenger:

```http
POST /passenger/request-ride
GET  /passenger/status/{ride_id}
POST /passenger/cancel
```

Driver:

```http
POST /driver/status
GET  /driver/requests
POST /driver/accept
POST /driver/start
POST /driver/complete
```

All endpoints:

```text
send command
return state
```

## Event System

Events:

```text
driver_assigned
trip_started
trip_completed
```

These events are enough for the Phase 1 MVP.

## Testing Plan

Level 1:

```bash
python3 -m afritech.demo.proof
```

Level 2 manual app test:

```text
passenger requests ride
driver receives request
driver accepts
driver starts trip
driver completes trip
```

Verify:

- correct state transitions
- no illegal transitions
- command flow is adapter-only

Level 3 failure case:

- driver drops connection
- retry action occurs
- cancel occurs

These tests validate interface behavior only. They do not expand the proof surface.

## Release Gate

Before any MVP release:

```bash
python3 -m afritech.demo.proof
```

The proof must preserve the same meaning, claims, and boundaries. If proof meaning changes, the MVP change is rejected.

## Non-Claims

This document does not claim:

- deployed passenger app
- deployed driver app
- production readiness
- live pilot readiness
- global deployment readiness
- new proof claims

## Governing Principle

```text
AfriTech defines truth.
AfriRide MVP tests interaction.
```
