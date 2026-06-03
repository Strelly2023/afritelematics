# AfriRide Controlled Pilot Runbook

Artifact Type: Execution Contract

Authority Level: Pilot Enforcement Layer

Pipeline: Constitutional (validated path required)

STATUS: CONTROLLED PILOT RUNBOOK CONTRACT

CLASSIFICATION: EXECUTABLE PILOT CONTRACT

This runbook defines the exact operational procedure for executing the AfriRide Controlled Pilot across all approved locations.

It is not an architecture document, not a design artifact, not a simulation, and not a production launch claim.

## Purpose

This runbook ensures that:

```text
- all scenarios are executed deterministically
- all evidence is captured
- all outcomes are replay-verifiable
- no uncontrolled behavior enters the system
```

## Mandatory Pilot Locations

```text
1. Melbourne (Australia) -> baseline
2. Bujumbura <-> Uvira -> infrastructure stress
3. Kinshasa -> behavioral + density stress
```

## Pre-Run Checklist

Pilot MUST NOT start unless all checks pass.

System readiness:

```text
API reachable
Queue ingestion active
Worker pool operational
Event log writable
Replay engine active
Proof generator active
```

Validator status:

```text
afriride_controlled_pilot_layer_validator -> PASS
afriride_controlled_pilot_scenario_matrix_validator -> PASS
constitutional_pipeline -> PASS
app_surface_validator -> PASS
```

Participant configuration:

```text
Riders registered (whitelisted)
Drivers registered (whitelisted)
Devices tested (GPS + network)
Identity consistency validated
```

Environment setup:

```text
Location boundaries configured
Time window set
Scenario set loaded
```

If any check fails:

```text
ABORT RUN (hard stop)
```

## Scenario Execution Order

Scenarios MUST be executed in this order:

```text
1. Baseline (Melbourne)
2. Infrastructure stress (Bujumbura/Uvira)
3. Behavioral stress (Kinshasa)
4. Global validation
```

Phase 1 - Melbourne:

```text
A1 -> A2 -> A3 -> A4 -> A5
```

Phase 2 - Bujumbura/Uvira:

```text
C1 -> C2 -> C3 -> D1 -> D2
```

Phase 3 - Kinshasa:

```text
E1 -> E2 -> E3 -> F1 -> F2 -> F3
```

Phase 4 - Global Validation:

```text
G1 -> G2 -> G3
```

## Incident Logging Format

All incidents MUST be recorded.

Required JSON fields:

```json
{
  "scenario_id": "E2",
  "location": "Kinshasa",
  "timestamp": "...",
  "event_id": "...",
  "failure_type": "duplicate_accept",
  "description": "...",
  "execution_hash": "...",
  "replay_hash": "...",
  "status": "PASS | FAIL | ISOLATED"
}
```

Rule:

```text
NO incident = no admissibility
```

## Evidence Capture

Every scenario MUST produce:

```text
Event log entries
Execution trace
Replay output
Proof receipt
UI confirmation (optional)
```

Evidence storage path:

```text
/storage/pilot_runs/{location}/{scenario_id}/
```

Evidence MUST be:

```text
Immutable
Timestamped
Hash-bound
```

## Replay Verification

For every scenario:

```text
Execution Hash == Replay Hash
```

Validation steps:

```text
1. Extract execution trace
2. Run replay_engine
3. Compare outputs
4. Store result
```

Failure:

```text
Replay mismatch -> IMMEDIATE SCENARIO FAIL
```

## Abort Conditions

Immediate abort if:

```text
Replay mismatch detected
Identity drift detected
Event missing in lifecycle
Non-deterministic output observed
Validator failure during run
```

Action:

```text
Stop entire pilot
Isolate failing scenario
Record incident
```

## Post-Run Report

Report structure:

```text
Pilot Run Summary:

Location: __________
Scenarios Executed: ___ / ___
Pass Count: ___
Fail Count: ___
Isolated Events: ___

Replay Success Rate: ___%
Identity Integrity: PASS / FAIL
Event Integrity: PASS / FAIL

Final Status:
ADMISSIBLE
or
REJECTED
```

Required attachments:

```text
Incident logs
Replay reports
Proof receipts
```

## Final Pass Criteria

Pilot is valid only if:

```text
ALL scenarios -> PASS or ISOLATED safely
AND Replay success = 100%
AND Identity drift = 0
AND No invariant violations
```

## Invalidation Conditions

Pilot is invalid if any:

```text
Replay mismatch
Identity mutation
Hidden execution path
Missing event transition
```

## Controlled Pilot Law

```text
A scenario is admissible IF AND ONLY IF:

Event -> Execution -> Replay -> Proof

remains consistent and verifiable
```

## Operator Discipline Rule

Operators must:

```text
FOLLOW execution order strictly
NOT skip scenarios
NOT modify system behavior
NOT override outcomes
```

## Final Classification

This runbook defines:

```text
Executable Pilot Contract

NOT:
Architecture
Design
Simulation

BUT:
Controlled real-world execution process
```

## Canonical Runbook Contract

```yaml
controlled_pilot_runbook:
  schema: afriride.controlled_pilot_runbook.v1
  status: controlled_pilot_runbook_contract
  classification: executable_pilot_contract
  artifact_type: execution_contract
  authority_level: pilot_enforcement_layer
  pipeline: constitutional
  production_launch_claimed: false
  simulation_only_claimed: false
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
    global_validation:
      - G1
      - G2
      - G3
  pre_run_checklist:
    system_readiness:
      - api_reachable
      - queue_ingestion_active
      - worker_pool_operational
      - event_log_writable
      - replay_engine_active
      - proof_generator_active
    validators:
      - afriride_controlled_pilot_layer_validator
      - afriride_controlled_pilot_scenario_matrix_validator
      - constitutional_pipeline
      - app_surface_validator
    participants:
      - riders_whitelisted
      - drivers_whitelisted
      - devices_tested
      - identity_consistency_validated
    environment:
      - location_boundaries_configured
      - time_window_set
      - scenario_set_loaded
  incident_required_fields:
    - scenario_id
    - location
    - timestamp
    - event_id
    - failure_type
    - description
    - execution_hash
    - replay_hash
    - status
  incident_status_values:
    - PASS
    - FAIL
    - ISOLATED
  mandatory_evidence:
    - event_log_entries
    - execution_trace
    - replay_output
    - proof_receipt
    - ui_confirmation_optional
  evidence_storage_path: /storage/pilot_runs/{location}/{scenario_id}/
  evidence_properties:
    - immutable
    - timestamped
    - hash_bound
  replay_verification_steps:
    - extract_execution_trace
    - run_replay_engine
    - compare_outputs
    - store_result
  abort_conditions:
    - replay_mismatch_detected
    - identity_drift_detected
    - event_missing_in_lifecycle
    - non_deterministic_output_observed
    - validator_failure_during_run
  abort_actions:
    - stop_entire_pilot
    - isolate_failing_scenario
    - record_incident
  post_run_report_fields:
    - location
    - scenarios_executed
    - pass_count
    - fail_count
    - isolated_events
    - replay_success_rate
    - identity_integrity
    - event_integrity
    - final_status
  required_attachments:
    - incident_logs
    - replay_reports
    - proof_receipts
  final_pass_criteria:
    - all_scenarios_pass_or_isolated_safely
    - replay_success_100_percent
    - identity_drift_zero
    - no_invariant_violations
  invalidation_conditions:
    - replay_mismatch
    - identity_mutation
    - hidden_execution_path
    - missing_event_transition
  operator_rules:
    - follow_execution_order_strictly
    - do_not_skip_scenarios
    - do_not_modify_system_behavior
    - do_not_override_outcomes
```
