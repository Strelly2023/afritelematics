# AfriRide Controlled Pilot Scenario Matrix

STATUS: CONTROLLED PILOT SCENARIO MATRIX

CLASSIFICATION: DETERMINISTIC FAILURE AND REAL-WORLD CASE CONTRACT

This artifact defines the controlled pilot scenario matrix for Melbourne, the Bujumbura to Uvira corridor, and Kinshasa. It is aligned with the AfriRide Controlled Pilot Layer and preserves deterministic execution, replay authority, event integrity, and failure isolation.

It is not a production launch plan and does not certify real-world operational success.

## Scenario Structure

Each scenario is defined by:

```text
Scenario Type -> Trigger -> Expected System Behavior -> Replay Condition -> Pass/Fail Criteria
```

## Location Profiles

```text
Melbourne -> controlled perfection baseline
Bujumbura/Uvira -> infrastructure stress
Kinshasa -> behavioral and scale stress
```

Together:

```text
System validity = survives ALL three environments
```

## Global Pass/Fail Gate

Pilot passes only if all scenarios satisfy:

```text
Replay stable
Deterministic output preserved
Proof generated
No invariant violation
```

Pilot fails if any scenario produces:

```text
Replay mismatch
Identity drift
Hidden state mutation
Non-deterministic behavior
```

## Final Pilot Scenario Law

```text
A pilot system is considered valid ONLY IF:

All realistic and adversarial scenarios
produce deterministic, replayable,
and provable outcomes across all environments.
```

## Canonical Scenario Matrix

```yaml
controlled_pilot_scenario_matrix:
  schema: afriride.controlled_pilot_scenario_matrix.v1
  status: controlled_pilot_scenario_matrix
  classification: deterministic_failure_and_real_world_case_contract
  production_launch_claimed: false
  operational_success_claimed: false
  truth_authority: replay_only
  scenario_structure:
    - scenario_type
    - trigger
    - expected_system_behavior
    - replay_condition
    - pass_fail_criteria
  locations:
    melbourne:
      profile:
        - stable_network
        - gps_precision
        - reliable_payment_systems
        - strict_regulatory_compliance
      scenarios:
        A1_normal_ride_completion:
          scenario_type: standard_high_reliability
          trigger: rider_requests_driver_accepts_trip_completes
          expected_system_behavior:
            - matching_deterministic
            - trip_executes_cleanly
            - payment_processed
          replay_condition: full_trace_reproducible
          pass_fail_criteria:
            pass: replay_hash_equals_execution_hash
            fail: replay_hash_differs_from_execution_hash
        A2_driver_reject_cascade:
          scenario_type: standard_high_reliability
          trigger: three_drivers_reject_sequentially
          expected_system_behavior:
            - matching_reassigns_deterministically
            - no_race_conditions
          replay_condition: same_driver_selected_every_time
          pass_fail_criteria:
            pass: same_assignment_on_replay
            fail: different_driver_selected_on_replay
        A3_rider_cancels_during_matching:
          scenario_type: standard_high_reliability
          trigger: cancel_before_driver_assigned
          expected_system_behavior:
            - event_recorded
            - matching_halted
          replay_condition: cancellation_event_stops_flow_identically
          pass_fail_criteria:
            pass: no_driver_assigned_after_cancel
            fail: driver_assigned_after_replay
        A4_network_delay_before_accept:
          scenario_type: failure_injection
          trigger: driver_receives_request_but_responds_late
          expected_system_behavior:
            - timeout_enforced_deterministically
            - request_reassigned
          replay_condition: same_timeout_decision
          pass_fail_criteria:
            pass: same_reassignment_on_replay
            fail: different_assignment_outcome
        A5_payment_failure_card_declined:
          scenario_type: failure_injection
          trigger: payment_api_returns_failure
          expected_system_behavior:
            - trip_marked_unpaid
            - no_state_corruption
          replay_condition: same_failure_outcome
          pass_fail_criteria:
            pass: unpaid_state_preserved
            fail: trip_becomes_paid_on_replay
    bujumbura_uvira:
      profile:
        - weak_network
        - border_crossing_complexity
        - cash_heavy_economy
        - gps_inaccuracies
      scenarios:
        C1_trip_crossing_border:
          scenario_type: cross_border_reality
          trigger: trip_starts_burundi_ends_drc
          expected_system_behavior:
            - single_trip_id_maintained
            - no_identity_drift
          replay_condition: exact_border_crossing_path_reconstructed
          pass_fail_criteria:
            pass: trip_identity_preserved
            fail: trip_splits_or_changes_identity
        C2_driver_loses_network_mid_trip:
          scenario_type: cross_border_reality
          trigger: driver_offline_for_5_to_10_minutes
          expected_system_behavior:
            - local_state_buffered
            - events_uploaded_later
          replay_condition: buffered_events_replay_correctly
          pass_fail_criteria:
            pass: no_missing_replay_segment
            fail: missing_segment_in_replay
        C3_delayed_event_submission:
          scenario_type: cross_border_reality
          trigger: trip_end_event_arrives_late
          expected_system_behavior:
            - ordering_preserved_by_timestamps
            - no_execution_divergence
          replay_condition: same_final_state
          pass_fail_criteria:
            pass: final_state_preserved
            fail: different_fare_or_route_outcome
        D1_gps_drift_wrong_location:
          scenario_type: low_infrastructure_failure
          trigger: driver_gps_jumps_location
          expected_system_behavior:
            - anomaly_filtered_or_recorded_deterministically
          replay_condition: same_anomaly_appears
          pass_fail_criteria:
            pass: route_reconstruction_stable
            fail: different_route_reconstruction
        D2_cash_payment_dispute:
          scenario_type: low_infrastructure_failure
          trigger: rider_claims_paid_driver_disagrees
          expected_system_behavior:
            - both_events_recorded
            - no_overwrite
          replay_condition: dispute_preserved
          pass_fail_criteria:
            pass: dispute_trace_preserved
            fail: system_resolves_without_trace
    kinshasa:
      profile:
        - dense_city_high_demand
        - traffic_variability
        - informal_behavior_patterns
        - device_network_inconsistency
      scenarios:
        E1_multiple_simultaneous_requests:
          scenario_type: high_load_behavior_variability
          trigger: high_demand_spike
          expected_system_behavior:
            - deterministic_partition_routing
            - no_cross_interference
          replay_condition: same_assignments
          pass_fail_criteria:
            pass: same_driver_allocations
            fail: different_driver_allocation
        E2_duplicate_accept_attempt:
          scenario_type: high_load_behavior_variability
          trigger: two_drivers_accept_same_request
          expected_system_behavior:
            - matching_resolves_deterministically
            - one_accepted_one_rejected
          replay_condition: same_winner
          pass_fail_criteria:
            pass: same_accept_winner
            fail: different_winner
        E3_route_deviation_by_driver:
          scenario_type: high_load_behavior_variability
          trigger: driver_deviates_from_suggested_route
          expected_system_behavior:
            - event_recorded_not_corrected
            - fare_determined_by_recorded_inputs
          replay_condition: same_route_deviation
          pass_fail_criteria:
            pass: deviation_preserved
            fail: route_normalized_differently
        F1_fake_trip_completion:
          scenario_type: adversarial_behavior
          trigger: driver_attempts_completion_without_pickup
          expected_system_behavior:
            - invariant_violation_detected
            - trip_flagged
          replay_condition: same_violation
          pass_fail_criteria:
            pass: violation_preserved
            fail: trip_passes_validation
        F2_rider_ghost_request_spam:
          scenario_type: adversarial_behavior
          trigger: rapid_repeated_requests
          expected_system_behavior:
            - filtered_or_rate_limited_deterministically
          replay_condition: same_acceptance_rejection_pattern
          pass_fail_criteria:
            pass: pattern_preserved
            fail: different_acceptance_behavior
        F3_manual_driver_status_toggle_abuse:
          scenario_type: adversarial_behavior
          trigger: driver_toggles_online_offline_rapidly
          expected_system_behavior:
            - state_transitions_recorded
            - matching_unaffected_deterministically
          replay_condition: same_availability_pattern
          pass_fail_criteria:
            pass: availability_pattern_preserved
            fail: different_matching_decision
  global_scenarios:
    G1_replay_integrity:
      law: execution_hash_equals_replay_hash
    G2_identity_invariance:
      law: trip_driver_rider_ids_never_change
    G3_event_completeness:
      law: request_match_start_end_present
  technical_metrics:
    replay_success_rate: "100%"
    event_integrity: "100%"
    identity_drift: "0"
    execution_divergence: "0"
  operational_metrics:
    trip_completion_rate: ">=95%"
    driver_response_time: stable
    cancellation_behavior: predictable
  failure_metrics:
    all_failures:
      - logged
      - replayable
      - isolated
  pass_gate:
    - replay_stable
    - deterministic_output_preserved
    - proof_generated
    - no_invariant_violation
  fail_gate:
    - replay_mismatch
    - identity_drift
    - hidden_state_mutation
    - non_deterministic_behavior
```
