# AfriRide Pilot Metrics Dashboard

Artifact Type: Operational Intelligence Layer

Purpose: Continuously observe, validate, enforce, and signal readiness during the controlled pilot.

STATUS: PILOT METRICS DASHBOARD CONTRACT

CLASSIFICATION: LIVE + CI ADMISSIBILITY SURFACE

The pilot metrics dashboard is a dual-system dashboard:

```text
LIVE DASHBOARD -> Operational Reality
CI DASHBOARD   -> Constitutional Truth
```

The dashboard does not define truth. It displays behavior and exposes admissibility state.

## Core Architecture

```text
Event Log
-> Replay Engine
-> Proof Layer
-> Live Dashboard
-> CI Dashboard
-> GO / NO-GO
```

## Live Dashboard

Purpose:

```text
Display real-world pilot execution in real time WITHOUT defining system truth.
```

Required sections:

```text
Trip Lifecycle Panel:
- active_trips
- completed_trips
- cancelled_trips
- trip_completion_rate
- average_trip_duration
- cancellation_rate

Scenario Execution Tracker:
- melbourne_a1_a5
- bujumbura_uvira_c1_d2
- kinshasa_e1_f3
- global_g1_g3

Location Panels:
- melbourne_baseline_stability
- bujumbura_uvira_offline_delayed_gps
- kinshasa_load_duplicate_accepts_volatility

Event Pipeline Health:
- adapter_success_rate
- normalization_success_rate
- queue_ingestion_rate
- event_rejection_count

Real-Time Failure Feed:
- replay_mismatches
- event_validation_errors
- timeout_events
- identity_checks

Actor Panels:
- drivers_online
- driver_acceptance_rate
- driver_dropoff_behavior
- rider_requests_per_minute
- rider_retry_patterns
- rider_cancellation_rate
```

## CI Dashboard

Purpose:

```text
Define system admissibility through constitutional validation.
```

Required panels:

```text
Constitutional Status Panel:
- invariants_pass_fail

Replay Integrity Panel:
- replay_success_rate
- mismatch_count

Identity Integrity Panel:
- trip_id_stability
- driver_id_stability
- rider_id_stability

Deterministic Execution Panel:
- same_input_same_output
- deviation_count

Evidence Bundle Status:
- bundle_completeness
- manifest_valid
- all_16_scenarios_present

Execution Receipt Status:
- execution_receipt_valid
- certification_generated

GO / NO-GO Panel:
- replay_ok
- evidence_ok
- receipt_ok
- certification_ok
- go_no_go

Validator Pipeline Status:
- pilot_layer_validator
- scenario_matrix_validator
- runbook_validator
- bundle_validator
- receipt_validator
- evidence_automation_validator
- certification_validator
- go_no_go_gate_validator
```

## Live vs CI Separation

```text
LIVE reflects behavior.
CI defines admissibility.
```

Golden rule:

```text
Live dashboard may show success.
CI dashboard decides if it is real success.
```

## Metrics Contract

```text
Tier 1 MUST NEVER FAIL:
- replay_success_rate == 100%
- identity_drift == 0
- execution_divergence == 0
- event_corruption == 0

Tier 2 Operational Indicators:
- trip_completion_rate >= 95%
- driver_acceptance_rate >= 70%
- matching_latency_stable == true

Tier 3 Diagnostic:
- network_performance
- gps_deviation
- user_behavior_anomalies
```

## Alerting System

```text
Critical Alerts:
- replay_mismatch
- identity_drift
- determinism_violation
- action: hard_stop_pilot

Warning Alerts:
- high_cancellation_rate
- driver_shortage
- slow_matching

Info Alerts:
- traffic_patterns
- demand_spikes
- usage_metrics
```

## Data Sources

```text
Primary Inputs:
- event_log
- replay_engine
- proof_layer
- ci_validators
- evidence_bundle
- execution_receipt

Derived Metrics:
- replay_success_percentage
- scenario_completion_percentage
- go_no_go_readiness
```

## Governance Constraints

Dashboards MUST NOT:

```text
- alter execution
- modify events
- override replay results
- influence CI decisions
```

## Dashboard Law

```text
Observability shows behavior.
Validation enforces discipline.
Replay defines truth.
CI defines admissibility.
```

## Execution Checkpoint Flow

```text
Run Pilot
-> Event Log Generated
-> Evidence Ingestion
-> Evidence Bundle
-> Bundle Validation
-> Execution Receipt
-> Receipt Validation
-> Certification
-> GO / NO-GO Decision
```

Critical truth chain:

```text
Execution -> Event -> Replay -> Evidence -> Receipt -> Certification -> Decision
```

Final boundary:

```text
Pilot Execution: READY TO RUN
Pilot Completion: NOT YET ACHIEVED until real execution happens
```

## Canonical Pilot Metrics Dashboard Contract

```yaml
pilot_metrics_dashboard:
  schema: afriride.pilot_metrics_dashboard.v1
  status: pilot_metrics_dashboard_contract
  classification: live_ci_admissibility_surface
  artifact_type: operational_intelligence_layer
  live_defines_truth: false
  ci_defines_admissibility: true
  replay_defines_truth: true
  pilot_execution_ready_to_run: true
  pilot_completion_claimed: false
  required_architecture:
    - event_log
    - replay_engine
    - proof_layer
    - live_dashboard
    - ci_dashboard
    - go_no_go
  live_sections:
    - trip_lifecycle_panel
    - scenario_execution_tracker
    - location_panels
    - event_pipeline_health
    - real_time_failure_feed
    - actor_panels
  ci_panels:
    - constitutional_status_panel
    - replay_integrity_panel
    - identity_integrity_panel
    - deterministic_execution_panel
    - evidence_bundle_status
    - execution_receipt_status
    - go_no_go_panel
    - validator_pipeline_status
  tier1_metrics:
    replay_success_rate: "100%"
    identity_drift: 0
    execution_divergence: 0
    event_corruption: 0
  tier2_metrics:
    trip_completion_rate_minimum: "95%"
    driver_acceptance_rate_minimum: "70%"
    matching_latency_stable: true
  critical_alerts:
    - replay_mismatch
    - identity_drift
    - determinism_violation
  critical_alert_action: hard_stop_pilot
  primary_inputs:
    - event_log
    - replay_engine
    - proof_layer
    - ci_validators
    - evidence_bundle
    - execution_receipt
  forbidden_dashboard_actions:
    - alter_execution
    - modify_events
    - override_replay_results
    - influence_ci_decisions
  execution_checkpoint_flow:
    - run_pilot
    - event_log_generated
    - evidence_ingestion
    - evidence_bundle
    - bundle_validation
    - execution_receipt
    - receipt_validation
    - certification
    - go_no_go_decision
```
