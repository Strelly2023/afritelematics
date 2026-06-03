# AfriRide Bujumbura Uvira Phase Execution Control

Artifact Type: Location Phase Execution Control

Mode: LIVE OPERATION

Purpose: Control Bujumbura/Uvira infrastructure-stress execution scenarios C1 through D2.

STATUS: BUJUMBURA UVIRA PHASE EXECUTION CONTROL CONTRACT

CLASSIFICATION: INFRASTRUCTURE STRESS EXECUTION CONTROL

This contract controls Bujumbura/Uvira Phase execution:

```text
C1 -> C2 -> C3 -> D1 -> D2
```

It does not claim that Bujumbura/Uvira execution has passed.

## Phase Objective

Validate continuity under degraded conditions:

```text
- event durability under network loss
- ordering consistency under delay
- identity continuity across regions
- deterministic handling of noisy sensor input
- neutral preservation of conflicting claims
```

Core phase law:

```text
Network conditions MAY vary.
Execution outcome MUST NOT vary.
```

## Scenario C1 — Cross-Border Trip Continuity

Objective:

```text
Validate that a Bujumbura to Uvira trip remains one continuous identity.
```

Required behavior:

```text
- same trip_id from start to end
- no split into multiple trips
- continuous event stream
- replay reconstructs complete journey
```

Evidence:

```text
- request_event
- match_event
- accept_event
- start_event
- location_events_cross_border
- end_event
- execution_hash
- replay_hash
```

Hard fail:

```text
trip splits OR identity changes
```

## Scenario C2 — Driver Offline Mid-Trip

Objective:

```text
Validate event durability and buffering during network loss.
```

Required behavior:

```text
- events generated locally while offline
- buffered events uploaded after reconnect
- original logical order preserved
- no duplicate events
- no missing offline segment
```

Evidence:

```text
- request_event
- match_event
- start_event
- buffered_events
- flush_events
- end_event
- execution_hash
- replay_hash
```

Hard fail:

```text
missing segment in replay
```

## Scenario C3 — Delayed Event Submission

Objective:

```text
Validate logical ordering over arrival-time ordering.
```

Expected behavior:

```text
arrival_order: E1 -> E3 -> E2
logical_order: E1 -> E2 -> E3
```

System must use logical sequence, not network arrival time.

Evidence:

```text
- event_1_sequence_id
- event_2_delayed
- event_3_sequence_id
- ingestion_timestamps
- logical_timestamps
- execution_hash
- replay_hash
```

Hard fail:

```text
late event changes execution outcome
```

## Scenario D1 — GPS Drift / Location Noise

Objective:

```text
Validate state integrity under incorrect sensor input.
```

Required behavior:

```text
- GPS anomaly recorded exactly as received
- no silent correction
- no invisible smoothing
- replay reproduces same anomaly
```

Evidence:

```text
- original_gps_events
- anomalous_jumps
- timing_data
- sequence_ids
- execution_hash
- replay_hash
```

Hard fail:

```text
replay produces different route
```

## Scenario D2 — Cash Payment Dispute

Objective:

```text
Validate neutral preservation of conflicting payment claims.
```

Required behavior:

```text
- trip_state == COMPLETED
- payment_mode == CASH
- rider_payment_claim == PAID
- driver_payment_claim == UNPAID
- payment_status == DISPUTED
- no automatic resolution
- no claim overwrite
```

Evidence:

```text
- end_event
- rider_payment_claim_event
- driver_payment_claim_event
- execution_hash
- replay_hash
```

Hard fail:

```text
system resolves dispute without trace
```

## Infrastructure Phase Hard Stops

Stop entire pilot immediately if any occurs:

```text
- event_loss
- replay_mismatch
- identity_drift
- event_ordering_break
- state_depends_on_network_timing
- trip_split
- duplicate_events
- silent_gps_correction
- claim_overwrite
- silent_dispute_resolution
```

## Phase Success Rule

```text
Bujumbura/Uvira phase is validated ONLY IF:
C1 PASS
AND C2 PASS
AND C3 PASS
AND D1 PASS
AND D2 PASS
AND replay_correctness == 100%
AND event_integrity == 100%
AND identity_drift == 0
AND ordering_preserved == true
```

## Operator Law

```text
The operator is not testing infrastructure quality.
The operator is testing whether the system is immune to infrastructure failure.
```

Operator must not:

```text
- fix missing data manually
- replay data manually
- stabilize network artificially
- ignore late events
- smooth GPS manually
- resolve disputes manually
```

Current state:

```text
Bujumbura/Uvira Phase Ready To Run: true
Bujumbura/Uvira Phase Passed: NOT CLAIMED
```

## Canonical Bujumbura/Uvira Phase Execution Control Contract

```yaml
bujumbura_uvira_phase_execution_control:
  schema: afriride.bujumbura_uvira_phase_execution_control.v1
  status: bujumbura_uvira_phase_execution_control_contract
  classification: infrastructure_stress_execution_control
  artifact_type: location_phase_execution_control
  location: Bujumbura_Uvira
  phase_ready_to_run: true
  phase_passed_claimed: false
  scenarios:
    - C1
    - C2
    - C3
    - D1
    - D2
  scenario_objectives:
    C1: cross_border_identity_continuity
    C2: buffered_event_integrity_under_offline
    C3: logical_ordering_over_arrival_time
    D1: gps_anomaly_preservation
    D2: conflicting_claims_preserved_neutrally
  required_sequences:
    C1:
      - request
      - match
      - accept
      - start
      - cross_border_location_events
      - end
    C2:
      - request
      - match
      - start
      - offline_buffered_events
      - reconnect_flush_events
      - end
    C3:
      - event_1_arrives
      - event_3_arrives
      - event_2_arrives_late
      - logical_order_reconstructed
    D1:
      - normal_gps_event
      - gps_anomaly_event
      - anomaly_preserved
      - end
    D2:
      - end
      - rider_paid_claim
      - driver_unpaid_claim
      - dispute_recorded
  hard_stops:
    - event_loss
    - replay_mismatch
    - identity_drift
    - event_ordering_break
    - state_depends_on_network_timing
    - trip_split
    - duplicate_events
    - silent_gps_correction
    - claim_overwrite
    - silent_dispute_resolution
  evidence_required:
    - request_event
    - match_event
    - accept_event
    - start_event
    - cross_border_location_events
    - buffered_events
    - flush_events
    - ingestion_timestamps
    - logical_timestamps
    - original_gps_events
    - anomalous_jumps
    - rider_payment_claim_event
    - driver_payment_claim_event
    - end_event
    - execution_hash
    - replay_hash
  completion_rule:
    all_scenarios_pass: true
    replay_correctness: "100%"
    event_integrity: "100%"
    identity_drift: 0
    ordering_preserved: true
  operator_law: system_immunity_to_infrastructure_failure
  forbidden_operator_actions:
    - fix_missing_data_manually
    - replay_data_manually
    - stabilize_network_artificially
    - ignore_late_events
    - smooth_gps_manually
    - resolve_disputes_manually
```
