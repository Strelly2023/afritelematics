# AfriRide City Pilot Playbook

STATUS: BOUNDED OPERATIONAL PILOT PLAN
CLASSIFICATION: GOVERNED OPERATIONAL SURFACE

## Governed Specification

```yaml
scope:
  description: Bounded city-level pilot for AfriRide mobility execution validation
  validates: bounded mobility execution under defined conditions
  explicitly_not_claimed:
    - global scalability
    - production readiness
    - production reliability guarantees
    - economic optimality
    - market proven
    - global deployment readiness

zones:
  melbourne:
    area: airport_to_cbd
    corridor: Melbourne Airport <-> Melbourne CBD
    reason: bounded geography + predictable traffic + local operational control
    first: true
    scale:
      drivers: 10-25
      riders: 50-200 invite-only
      trips_per_day: 50-150
  burundi:
    area: bujumbura_core
    reason: high entropy validation
    second: true
    stressors:
      - unstable mobile networks
      - low-end devices
      - inconsistent GPS
      - intermittent power
      - cash plus mobile-money payment observations

components:
  - driver_app
  - rider_app
  - edge_adapter
  - normalization_pipeline
  - admission_gate
  - event_queue
  - execution_engine
  - witness_store
  - replay_engine

event_pipeline:
  - reality_event
  - edge_ingestion
  - normalization
  - admission
  - queue
  - execution
  - witness
  - replay

scenarios:
  - name: trip_execution
    verifies:
      - full lifecycle replay
      - no missing events
      - mutation witness chain
  - name: gps_noise
    verifies:
      - deterministic normalization
      - replay-stable path
      - invalid jump rejection
  - name: offline_sync
    verifies:
      - convergence after reconnect
      - duplicate delivery collapse
      - clock drift normalization
  - name: adversarial_injection
    verifies:
      - rejection of invalid events
      - payload tamper rejection
      - unauthorized mutation rejection
  - name: network_delay
    verifies:
      - convergence under reordering
      - network event replay
      - delayed sync stability
  - name: surge_conditions
    verifies:
      - deterministic pricing
      - bounded surge
      - fairness enforcement

metrics:
  replay_success_rate:
    target: 100%
  trace_completeness:
    target: 100%
  convergence_divergence:
    target: 0
  security_breach:
    target: 0 successful
  determinism_variance:
    target: 0
  unauthorized_mutation:
    target: 0

phases:
  - phase_1_internal
  - phase_2_controlled
  - phase_3_expanded

failure_conditions:
  - replay divergence detected
  - normalization nondeterminism
  - convergence failure
  - unauthorized mutation success
  - trace completeness below target
  - pilot scope escape

evidence_package:
  - pilot_scope_receipt
  - normalized_event_trace
  - authenticated_mutation_trace
  - network_event_replay
  - convergence_trace_validation
  - pricing_replay_equivalence
  - fairness_trace_validation
  - real_trip_reconstruction
  - production_replay_trace
```

## Operating Rule

The pilot is an executable specification for bounded validation. It does not
grant production authority, global readiness authority, market-proof authority,
or deployment truth.

The only admissible pilot claim is:

```text
This pilot validates bounded mobility execution under defined conditions.
```

## Constitutional Pipeline

```text
REALITY EVENT
-> EDGE INGESTION
-> NORMALIZATION
-> ADMISSION
-> QUEUE
-> EXECUTION
-> WITNESS
-> REPLAY
```

## Termination Rule

Any failure condition stops claim escalation until the relevant trace,
normalization receipt, rejection record, witness chain, or replay reconstruction
is reviewed.
