# AfriRide Pilot Activation Checklist

Status: ACTIVATION PREPARED, LIVE GO NOT AUTHORIZED

Use this checklist only after repository-side protocol validation passes. Do not start real riders until all live gates are true.

## Phase 1: Backend Gate

- Confirm Render service is deployed from `main`
- Confirm start command is `uvicorn afriride_system.api.main:app --host 0.0.0.0 --port $PORT`
- Confirm `GET /health` returns `200 OK`
- Confirm `POST /v1/events` returns `200` or `201`
- Confirm `OPTIONS /rides/active` passes CORS
- Confirm `/ws/{ride_id}` connects or mobile fallback is enabled

## Phase 2: Device Gate

- Register `driver_phone_001`
- Register `rider_phone_001`
- Register `operator_laptop_001`
- Install Driver APK
- Install Rider APK
- Open Operator dashboard
- Confirm signed event emission from each real device

## Phase 3: Multi-Node Protocol Gate

- Run hardening suite
- Run adversarial attack suite
- Run AfriRide ledger scenario
- Confirm consensus blocks commit
- Confirm chain verification passes
- Confirm state projection returns completed ride and receipt

## Phase 4: Evidence Gate

- Create `traces/pilot_runs/live_pilot_001`
- Capture signed event log
- Capture ride lifecycle trace
- Capture receipt
- Capture replay result
- Capture operator observation log
- Capture incident log
- Export evidence bundle

## Activation Rule

Activation is authorized only when:

```text
repo_side_ready = true
live_gates_all_true = true
operator_observer_ready = true
emergency_contact_ready = true
manual_truth_editing_disabled = true
```

Until then:

```text
go_authorized = false
live_pilot = HOLD
```
