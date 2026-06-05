# AfriRide Multi-Node Production Pilot Preparation

Status: PREPARED, NOT AUTHORIZED

This document prepares the AfriRide distributed coordination pilot. It does not authorize live rider execution.

## Deployment Topology

- Backend API: `https://afriride-api.onrender.com`
- Pilot run: `live_pilot_001`
- Nodes: `node-a`, `node-b`, `node-c`, `node-d`, `node-e`
- Devices: `driver_phone_001`, `rider_phone_001`, `operator_laptop_001`
- Apps: Driver APK, Rider APK, Operator dashboard

## Protocol Flow

1. Rider request emitted as signed event
2. Driver match contract executes across nodes
3. Pricing contract executes across nodes
4. Trip completion contract executes across nodes
5. Proofs are finalized by consensus
6. Accepted proofs commit into `AuditLedger`
7. Ledger-derived state projects ride and receipt
8. Replay and observability exports are captured

## Required Repo-Side Validators

```bash
python3 -m pytest afritech/tests/distributed/test_sovereign_ledger_protocol.py
python3 -m pytest afritech/tests/distributed/test_protocol_hardening_and_adversarial.py
python3 -m afritech.ci.app_surface_validator
python3 -m afritech.ci.driver_surface_validator
python3 -m afritech.ci.afriride_live_pilot_protocol_validator
python3 -m afritech.ci.afriride_field_validator
```

## Production Pilot Go / No-Go

GO only if all are true:

- Render health returns `200 OK`
- `OPTIONS /rides/active` CORS check passes
- `POST /v1/events` returns `200` or `201`
- WebSocket ride tracking connects or app fallback is enabled
- Driver APK installed on registered driver phone
- Rider APK installed on registered rider phone
- Operator dashboard can observe signed events
- Replay export works
- Evidence folder exists for `live_pilot_001`
- Emergency contact ready
- Manual truth editing disabled

NO-GO if any are true:

- Render health returns `503`
- `/v1/events` fails
- signed events are not emitted
- replay bundle cannot be exported
- device is unregistered
- driver app writes against a hard-coded ride id

## Evidence Bundle Target

The first production pilot evidence bundle must include:

- `device_registration_snapshot.json`
- `signed_event_log.jsonl`
- `ride_lifecycle_trace.json`
- `receipt.json`
- `replay_result.json`
- `evidence_bundle.json`
- `operator_observation_log.json`
- `incident_log.json`
- `post_pilot_report.md`

## Final Classification

- Repository protocol: pilot-prepared
- Multi-node simulation: required before live pilot
- Production pilot: HOLD until live backend and device gates pass
