# AfriRide Pilot Execution Checklist

Artifact Type: Live Operator Checklist

Mode: LIVE OPERATION

Purpose: Execute the controlled pilot safely and produce admissible evidence.

STATUS: PILOT EXECUTION CHECKLIST CONTRACT

CLASSIFICATION: OPERATOR LIVE CHECKLIST

Rule:

```text
Do NOT skip steps.
```

This checklist controls field execution. It does not claim that execution has occurred.

## Phase 0 — Control Init

Confirm execution authorization:

```text
- Wave 6 Execution Checkpoint = PASSED
- All validators = PASS
- No active system errors
```

Declare pilot session:

```text
pilot_session_id = UUID
timestamp = start_time
```

Lock system state:

```text
Freeze:
- pricing
- driver_pool
- matching_parameters

Disable:
- experimental_flags
- non_deterministic_features
```

Abort condition:

```text
If any instability is detected -> ABORT BEFORE START
```

## Phase 1 — Pre-Run Hard Gate

System health:

```text
- API responding
- queue active
- worker pool stable
- event log writable
- replay engine running
- proof system active
```

Validator status:

```text
- pilot_layer_validator -> PASS
- scenario_matrix_validator -> PASS
- runbook_validator -> PASS
- bundle_validator -> PASS
- receipt_validator -> PASS
```

Participant setup:

```text
- riders whitelisted
- drivers whitelisted
- IDs verified with no duplicates
- participants assigned to correct location
```

Device readiness:

```text
- GPS working
- network confirmed
- device registered
```

Scenario readiness:

```text
- all 16 scenarios loaded
- location mapping correct
```

Abort condition:

```text
If any pre-run check fails -> ABORT PILOT
```

## Phase 2 — Execution Strict Order

Melbourne baseline:

```text
A1 -> A2 -> A3 -> A4 -> A5
```

Bujumbura_Uvira infrastructure stress:

```text
C1 -> C2 -> C3 -> D1 -> D2
```

Kinshasa behavioral stress:

```text
E1 -> E2 -> E3 -> F1 -> F2 -> F3
```

Global validation:

```text
G1 -> G2 -> G3
```

For each scenario:

```text
1. trigger rider request
2. allow matching
3. execute trip lifecycle
4. confirm completion
```

Live checks:

```text
- event logged
- matching deterministic
- trip completed properly
- no duplicate events
```

Immediate stop conditions:

```text
replay_mismatch -> STOP
identity_drift -> STOP
missing_event -> STOP
```

## Phase 3 — Live Incident Logging

For any issue, log immediately:

```json
{
  "scenario_id": "...",
  "location": "...",
  "issue": "...",
  "event_id": "...",
  "timestamp": "...",
  "status": "RECORDED"
}
```

Rule:

```text
NO silent failures allowed.
```

## Phase 4 — Evidence Generation

Trigger evidence ingestion pipeline.

System must generate:

```text
- participant_registry.json
- device_registry.json
- 16 scenario receipts
- replay receipts
- incident logs
- summary
- manifest
```

Validate bundle:

```text
bundle_validator -> VALID or REJECTED
```

## Phase 5 — Replay Verification

For all scenarios:

```text
execution_hash == replay_hash
```

Abort condition:

```text
If any mismatch exists -> PILOT INVALID -> STOP
```

## Phase 6 — Execution Receipt

Generate only if bundle is valid:

```text
execution_receipt.json
```

Validate:

```text
receipt_validator -> PASS
```

## Phase 7 — Certification

Generate certificate:

```text
CONTROLLED_PILOT_CERTIFIED
```

Verify:

```text
- replay_verified == true
- identity_integrity == true
- all scenarios executed
```

## Phase 8 — Go/No-Go Decision

Evaluate:

```text
- replay == 100%
- identity_drift == 0
- evidence_bundle_valid == true
- receipt_valid == true
- certification_generated == true
```

Decision:

```text
If all true -> GO -> authorize Wave 7
If any fail -> NO-GO -> isolate issue -> fix system -> re-run pilot
```

## Phase 9 — Final Output

Deliverables:

```text
- Evidence Bundle
- Execution Receipt
- Certification Artifact
- GO / NO-GO Decision
```

## Final Operator Law

```text
You are NOT validating success.
You are validating truth.
```

Final checkpoint:

```text
- every scenario executed
- every event recorded
- every replay identical
- every failure logged
- certification validated
```

Current state:

```text
Live Pilot: READY TO RUN
Pilot Executed: NOT CLAIMED
```

## Canonical Pilot Execution Checklist Contract

```yaml
pilot_execution_checklist:
  schema: afriride.pilot_execution_checklist.v1
  status: pilot_execution_checklist_contract
  classification: operator_live_checklist
  artifact_type: live_operator_checklist
  live_pilot_ready_to_run: true
  pilot_executed_claimed: false
  no_step_skipping_allowed: true
  phases:
    - control_init
    - pre_run_hard_gate
    - execution_strict_order
    - live_incident_logging
    - evidence_generation
    - replay_verification
    - execution_receipt
    - certification
    - go_no_go_decision
    - final_output
  control_init_checks:
    - wave6_execution_checkpoint_passed
    - all_validators_pass
    - no_active_system_errors
    - pilot_session_declared
    - system_state_locked
  frozen_configuration:
    - pricing
    - driver_pool
    - matching_parameters
  disabled_features:
    - experimental_flags
    - non_deterministic_features
  pre_run_checks:
    - api_responding
    - queue_active
    - worker_pool_stable
    - event_log_writable
    - replay_engine_running
    - proof_system_active
    - riders_whitelisted
    - drivers_whitelisted
    - ids_verified_no_duplicates
    - gps_working
    - network_confirmed
    - device_registered
    - all_16_scenarios_loaded
    - location_mapping_correct
  scenario_order:
    melbourne:
      - A1
      - A2
      - A3
      - A4
      - A5
    bujumbura_uvira:
      - C1
      - C2
      - C3
      - D1
      - D2
    kinshasa:
      - E1
      - E2
      - E3
      - F1
      - F2
      - F3
    global:
      - G1
      - G2
      - G3
  immediate_stop_conditions:
    - replay_mismatch
    - identity_drift
    - missing_event
  evidence_outputs:
    - participant_registry.json
    - device_registry.json
    - scenario_receipts
    - replay_receipts
    - incident_logs
    - summary
    - manifest
  final_deliverables:
    - evidence_bundle
    - execution_receipt
    - certification_artifact
    - go_no_go_decision
  operator_law: validate_truth_not_success
```
