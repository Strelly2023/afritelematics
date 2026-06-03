# Melbourne Pilot Execution Checklist

STATUS: CONTROLLED PILOT EXECUTION CHECKLIST
CLASSIFICATION: OPERATIONAL READINESS ARTIFACT

This checklist does not claim production readiness, public launch readiness, or
market validation. It defines the minimum controlled conditions for executing an
internal AfriRide pilot in Melbourne.

## Phase 0 - Pre-Flight

- Backend deployed through the pilot Docker stack.
- `/v1/events` accepts signed mobile event batches.
- `/ws/{ride_id}` serves observation-only ride projections.
- Trace recorder is active for every pilot trip.
- Replay inspector can load recorded traces.
- JWT token issuance works for pilot users.
- Device registration binds user, device, and public key.
- Payment adapters emit payment events only.

## Phase 1 - Internal Test

- Simulate driver event stream.
- Simulate rider request flow.
- Complete 10 to 20 synthetic trips.
- Record every trace.
- Run replay readiness checks on every trace.

Required exit evidence:

- replay readiness status is `ready` for every complete trace.
- trace hash recomputation matches recorded hash.
- no duplicate event execution is observed.

## Phase 2 - Controlled Drivers

- Use 3 to 5 test drivers.
- Use internal rider accounts only.
- Capture real GPS observations.
- Test offline buffering and reconnect sync.
- Compare live projection updates with recorded event traces.

Required exit evidence:

- GPS events normalize without schema rejection drift.
- WebSocket lag is measured as projection latency only.
- offline sync preserves per-device logical clock order.

## Phase 3 - Limited Pilot

- Use 10 to 25 drivers.
- Use invite-only riders.
- Restrict geography to the Airport to CBD corridor.
- Keep support and manual review active during pilot windows.

## Day-One Human Execution Script

This section is a human-readable operating checklist for the sealed day-one
runbook. It does not replace:

- `reports/afriride_live_pilot_protocol_v1/day_one_runbook.json`
- `reports/afriride_live_pilot_protocol_v1/post_pilot_analysis.json`
- replay validators
- CI validators

The checklist may coordinate people and devices only. It may not define truth,
certify pilot completion, or authorize production readiness.

### Required Roles

- Pilot controller: opens and closes the pilot window, enforces stop conditions.
- Proof operator: runs validators, records hashes, captures evidence receipts.
- Support operator: runs dispute drills through replay authority only.
- Safety observer: may stop field movement for safety without changing proof truth.
- Driver cohort: executes only the scripted driver actions.
- Rider cohort: executes only the scripted rider actions.

### Evidence Folder

Before starting, create or select an evidence folder for the day-one run.

It must contain only captured evidence and validator outputs. Do not place
marketing notes, readiness claims, investor summaries, or manual truth decisions
inside the evidence folder.

### Minute-by-Minute Actions

| Minute | Owner | Human Action | Evidence Required | Stop If |
| --- | --- | --- | --- | --- |
| 0 | Pilot controller | Open the pilot window and read the claim boundary aloud. | `pilot_controller_closeout` opened | Anyone treats the pilot as production authority |
| 15 | Proof operator | Register all driver and rider devices and confirm signatures. | `device_registration_snapshot` | Any device is unsigned, unbound, or unknown |
| 30 | Proof operator | Run preflight validators before field movement. | `preflight_validator_receipt` | Any validator fails |
| 45 | Pilot controller | Execute one stationary dry-run trip and replay the trace. | `dry_run_trace_receipt` | Replay readiness is not `ready` |
| 75 | Driver cohort | Execute offline trip script with controlled disconnect and reconnect. | `offline_trip_trace` | Buffered events cannot replay equivalently |
| 105 | Proof operator | Execute delayed sync script and replay late-arriving events. | `delayed_sync_trace` | Canonical replay changes final truth |
| 135 | Driver cohort | Capture GPS drift along the bounded route. | `gps_drift_trace` | GPS normalization changes pricing truth |
| 165 | Proof operator | Submit duplicate signed event batches and verify idempotence. | `duplicate_events_trace` | Duplicate delivery causes duplicate execution |
| 195 | Support operator | Run dispute drill through replay authority only. | `dispute_resolution_trace` | Support outcome diverges from replay authority |
| 225 | Proof operator | Generate proof dashboard snapshot from collected traces. | `proof_dashboard_snapshot` | Dashboard reports drift or missing evidence |
| 240 | Pilot controller | Close the pilot window and record no-claim escalation decision. | `pilot_controller_closeout` closed | Any non-claim is violated |

### Operator Commands

The proof operator must run these commands before any external communication:

```text
python3 -m afritech.ci.afriride_live_pilot_protocol_validator
python3 -m afritech.ci.afriride_day_one_runbook_validator
python3 -m afritech.ci.afriride_post_pilot_analysis_validator
python3 -m afritech.ci.afriride_stakeholder_evidence_report_validator
```

### Communication Rule

Until post-pilot analysis accepts submitted evidence, the only permitted
stakeholder report state is:

```text
not_submitted
```

Do not say:

```text
pilot completed
production ready
public launch ready
regulatory approved
market validated
```

## Metrics

- replay success rate target: 100%
- divergence target: 0
- authentication bypass target: 0
- missing event target: 0
- payment reconciliation discrepancy target: 0
- WebSocket lag: measured, not authoritative
- ingestion rejection rate: monitored and explained

## Stop Conditions

- replay mismatch.
- missing mandatory lifecycle events.
- double execution of one event.
- authentication bypass.
- unauthorized device mutation.
- unfair allocation detected.
- payment event cannot be reconciled to provider evidence.

## Claim Boundary

The pilot may claim bounded execution evidence only after traces are captured and
validated. It may not claim production reliability, market readiness, regulatory
approval, or public launch readiness.
