# AfriRide Melbourne Phase Execution Control

Artifact Type: Location Phase Execution Control

Mode: LIVE OPERATION

Purpose: Control Melbourne baseline execution scenarios A1 through A5.

STATUS: MELBOURNE PHASE EXECUTION CONTROL CONTRACT

CLASSIFICATION: LOCATION BASELINE EXECUTION CONTROL

This contract controls Melbourne Phase execution:

```text
A1 -> A2 -> A3 -> A4 -> A5
```

It does not claim that Melbourne execution has passed.

## Scenario A1 — Normal Ride Completion

Objective:

```text
Validate full deterministic ride lifecycle.
```

Required sequence:

```text
request -> match -> accept -> start -> route -> end -> payment_event
```

Evidence:

```text
- request_event
- match_event
- accept_event
- start_event
- route_events
- end_event
- execution_hash
```

Pass condition:

```text
execution_hash == replay_hash
AND lifecycle complete
AND identity_integrity == true
AND event_integrity == true
```

## Scenario A2 — Driver Reject Cascade

Objective:

```text
Validate deterministic reassignment under sequential driver rejection.
```

Expected driver sequence:

```text
driver_1 -> reject
driver_2 -> reject
driver_3 -> accept
```

Evidence:

```text
- assignment_event_1
- reject_event_1
- assignment_event_2
- reject_event_2
- assignment_event_3
- accept_event
- start_event
- end_event
- execution_hash
```

Fail conditions:

```text
- different driver order on replay
- different final driver selected
- rejected driver reused incorrectly
- competing accept event
```

## Scenario A3 — Rider Cancellation During Matching

Objective:

```text
Validate that cancellation before acceptance halts matching deterministically.
```

Expected sequence:

```text
request_event -> matching_started_event -> cancel_event
```

Forbidden post-cancel activity:

```text
- driver assignment after cancellation
- accept event after cancellation
- matching continuation after cancellation
```

Evidence:

```text
- request_event
- matching_started_event
- cancel_event
- execution_hash
```

## Scenario A4 — Network Delay / Timeout Determinism

Objective:

```text
Validate deterministic timeout behavior under delayed driver response.
```

Expected sequence:

```text
driver_1 -> timeout
driver_2 -> accept
```

Evidence:

```text
- request_event
- assignment_event_driver_1
- timeout_event
- assignment_event_driver_2
- accept_event
- start_event
- end_event
- execution_hash
```

Temporal rule:

```text
Timeout must be based on deterministic event ordering and rules,
not wall-clock drift or device/network speed.
```

## Scenario A5 — Payment Failure Determinism

Objective:

```text
Validate that payment failure after trip completion does not corrupt trip state.
```

Required state separation:

```text
trip_state == COMPLETED
payment_state == FAILED
state_isolation == true
```

Expected replay sequence:

```text
request -> match -> accept -> start -> end -> payment_attempt -> payment_failed
```

Evidence:

```text
- request_event
- match_event
- accept_event
- start_event
- end_event
- payment_attempt_event
- payment_failed_event
- execution_hash
```

## Melbourne Hard Stops

Stop immediately if any occurs:

```text
- replay_mismatch
- identity_drift
- missing_event
- duplicate_assignment
- accept_conflict
- post_cancel_assignment
- timeout_race
- payment_state_corrupts_trip_state
```

## Melbourne Phase Completion Rule

```text
Melbourne phase is validated ONLY IF:
A1 PASS
AND A2 PASS
AND A3 PASS
AND A4 PASS
AND A5 PASS
AND all execution_hash values equal replay_hash values.
```

## Operator Law

```text
The operator preserves evidence, stops on invalidity, and lets replay decide truth.
```

Operator must not:

```text
- fix data during execution
- ignore anomalies
- force completion
- manually declare success
- retry payment during A5
- override replay mismatch
```

Current state:

```text
Melbourne Phase Ready To Run: true
Melbourne Phase Passed: NOT CLAIMED
```

## Canonical Melbourne Phase Execution Control Contract

```yaml
melbourne_phase_execution_control:
  schema: afriride.melbourne_phase_execution_control.v1
  status: melbourne_phase_execution_control_contract
  classification: location_baseline_execution_control
  artifact_type: location_phase_execution_control
  location: Melbourne
  phase_ready_to_run: true
  phase_passed_claimed: false
  scenarios:
    - A1
    - A2
    - A3
    - A4
    - A5
  scenario_objectives:
    A1: deterministic_ride_lifecycle
    A2: deterministic_reassignment_under_rejection
    A3: cancellation_halts_matching
    A4: deterministic_timeout_under_delay
    A5: payment_failure_state_isolation
  required_sequences:
    A1:
      - request
      - match
      - accept
      - start
      - route
      - end
      - payment_event
    A2:
      - driver_1_reject
      - driver_2_reject
      - driver_3_accept
    A3:
      - request_event
      - matching_started_event
      - cancel_event
    A4:
      - driver_1_timeout
      - driver_2_accept
    A5:
      - request
      - match
      - accept
      - start
      - end
      - payment_attempt
      - payment_failed
  hard_stops:
    - replay_mismatch
    - identity_drift
    - missing_event
    - duplicate_assignment
    - accept_conflict
    - post_cancel_assignment
    - timeout_race
    - payment_state_corrupts_trip_state
  evidence_required:
    - request_event
    - match_event
    - accept_event
    - start_event
    - route_events
    - end_event
    - assignment_events
    - reject_events
    - cancel_event
    - timeout_event
    - payment_attempt_event
    - payment_failed_event
    - execution_hash
    - replay_hash
  completion_rule:
    all_scenarios_pass: true
    all_hashes_match: true
    identity_integrity: true
    event_integrity: true
  operator_law: preserve_evidence_stop_on_invalidity_replay_decides_truth
  forbidden_operator_actions:
    - fix_data_during_execution
    - ignore_anomalies
    - force_completion
    - manually_declare_success
    - retry_payment_during_a5
    - override_replay_mismatch
```
