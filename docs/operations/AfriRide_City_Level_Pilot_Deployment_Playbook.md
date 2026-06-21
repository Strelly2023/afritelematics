# AfriRide City-Level Pilot Deployment Playbook

STATUS: BOUNDED OPERATIONAL PILOT PLAN
CLASSIFICATION: PILOT READINESS PLANNING SURFACE
GOVERNANCE MODE: REALITY -> NORMALIZATION -> ADMISSION -> EXECUTION -> WITNESS -> REPLAY

## Document Boundary

This playbook defines a bounded city-level pilot path for AfriRide.

It is not runtime authority, replay authority, proof authority, production
deployment proof, compliance certification, or payment licensing proof.

It is not evidence that AfriRide has completed a real-world city pilot.

It must not be used to claim:

```text
controlled city pilot completed
real-world mobility network readiness achieved
global deployment readiness achieved
production deployment readiness achieved
regulatory approval achieved
```

## Pilot Objective

Prove that real mobility operations can remain admissible under controlled
production-like conditions.

The pilot tests whether:

```text
human behavior
GPS noise
mobile latency
offline sync
payment observations
security pressure
market imbalance
```

can be reduced into:

```text
normalized events
admitted mutations
witness-backed execution
replay-stable traces
```

## Recommended Sequence

```text
1. Melbourne controlled corridor pilot
2. hardening and evidence review
3. Burundi stress pilot
```

Melbourne is the recommended first pilot because reliable network conditions,
high device quality, and local operational control isolate system behavior before
environmental stress is increased.

Burundi is the recommended second pilot because unstable network conditions,
lower-end devices, inconsistent GPS, intermittent power, and hybrid payments test
whether the normalization and replay model survives harsher real-world entropy.

## Melbourne Pilot

### Zone

```text
Melbourne Airport <-> Melbourne CBD corridor
```

The corridor is bounded, operationally legible, and suitable for repeatable
airport transfer trips.

### Scale

```text
drivers: 10-25
riders: 50-200 invite-only
fleet_type: cars only
trip_volume: 50-150 trips/day
duration: 2-8 weeks across staged rollout
```

### Client Surfaces

Driver app:

```text
trip accept/reject
GPS streaming
offline buffering
reconnect sync through normalization
driver status observations
```

Rider app:

```text
ride request
driver tracking from normalized GPS
pickup confirmation
dropoff confirmation
payment trigger event
```

## Burundi Pilot

### Purpose

Test AfriRide under higher operational disorder after the Melbourne evidence
review is complete.

### Stress Conditions

```text
unstable mobile networks
low-end devices
inconsistent GPS
intermittent power
cash plus mobile-money payment observations
offline driver operation
delayed sync bursts
dispute-prone cancellation and payment events
```

### Required Proof Focus

```text
extreme normalization
offline convergence
hybrid payment replay
delayed ingestion resilience
dispute trace reconstruction
```

## End-to-End Data Flow

All pilot inputs must pass through the constitutional edge path:

```text
Driver / Rider App
-> Edge Adapter
-> Normalization
-> Admission
-> Queue
-> Execution Engine
-> Witness Store
-> Replay System
```

No mobile client, public API, payment observation, or GPS reading may call core
runtime mutation directly.

## Pilot Test Matrix

### Real Trip Execution

Test:

```text
ride request
driver match
pickup
dropoff
payment observation
```

Evidence:

```text
trip_replay_trace
mutation_witness_chain
full_lifecycle_reconstruction
```

Acceptance:

```text
replay reconstructs full ride
no missing admitted events
no ordering violations
```

### GPS Reality vs Normalization

Inject:

```text
urban GPS drift
tunnel or airport signal loss
jitter
physically implausible jump
```

Evidence:

```text
normalized_gps_trace
gps_rejection_trace
route_replay_hash
```

Acceptance:

```text
physical path -> normalized observations -> replay-stable trace
```

### Network Behavior

Inject:

```text
latency
mobile disconnect
delayed sync
reordered delivery
```

Evidence:

```text
network_event_replay
convergence_trace_validation
offline_rejoin_hash
```

Acceptance:

```text
network chaos creates no replay divergence
```

### Client Chaos

Inject:

```text
offline driver
reconnect burst
duplicate event send
clock skew
```

Evidence:

```text
clock_drift_normalization_receipt
duplicate_delivery_rejection_trace
client_reconnect_trace
```

Acceptance:

```text
normalization collapses client chaos safely
```

### Security Layer

Inject:

```text
duplicate event injection
modified payload attempt
forged lineage
replay mutation attempt
```

Evidence:

```text
authenticated_mutation_trace
payload_tamper_rejection_trace
lineage_rejection_trace
replay_mutation_rejection_trace
```

Acceptance:

```text
invalid mutations are rejected before state mutation eligibility
```

### Market Dynamics

Simulate:

```text
peak hour demand
driver shortage
zero supply event
duplicate allocation attempt
```

Evidence:

```text
pricing_replay_equivalence
surge_stability_trace
fairness_trace_validation
market_imbalance_trace
```

Acceptance:

```text
pricing remains deterministic
surge remains bounded
matching remains fair
```

## Success Metrics

System metrics:

```text
replay_success: 100%
trace_completeness: 100%
determinism_variance: 0
convergence_failure: 0
```

Operational metrics:

```text
trip_completion: greater than 95%
driver_acceptance: greater than 80%
rider_satisfaction: qualitative evidence collected
```

Security metrics:

```text
forged_event_success: 0
unauthorized_mutation: 0
replay_attack_success: 0
```

## Safety Controls

Hard limits:

```text
bounded pilot zone
invite-only riders
approved driver roster
pricing cap
trip volume cap
manual operational stop
manual dispute review
```

Observability requirements:

```text
every raw observation logged outside core authority
every normalized event trace retained
every admission decision recorded
every mutation witness retained
every rejection recorded
every replay trace reconstructable
```

## Rollout

### Phase 1 - Internal Pilot

Duration:

```text
2 weeks
```

Scope:

```text
test drivers only
synthetic or staff riders
Melbourne corridor only
full replay verification after every trip
```

Exit criteria:

```text
100% replay success
0 determinism variance
0 unauthorized mutations
all failed trips classified with replay evidence
```

### Phase 2 - Controlled Users

Duration:

```text
2-4 weeks
```

Scope:

```text
invite-only riders
limited geography
bounded trip volume
manual support coverage
daily replay audit
```

Exit criteria:

```text
trip completion greater than 95%
driver acceptance greater than 80%
0 convergence failures
0 successful forged events
```

### Phase 3 - Open Pilot

Scope:

```text
expanded zone
increased volume
real operational stress
replay audit sampling plus incident-triggered full reconstruction
```

Exit criteria:

```text
pilot_scope_receipt
real_trip_reconstruction
production_replay_trace
controlled city pilot evidence package
```

## Evidence Package

Before any claim escalation, the pilot must produce:

```text
pilot_scope_receipt
normalized_event_trace
authenticated_mutation_trace
network_event_replay
convergence_trace_validation
pricing_replay_equivalence
fairness_trace_validation
real_trip_reconstruction
production_replay_trace
incident_rejection_log
```

## Safe Final Classification

This playbook defines how AfriRide may gather bounded city-level pilot evidence
without converting pilot planning into production truth.

The pilot question is:

```text
does reality stay admissible under execution?
```

not:

```text
does the app merely appear to work?
```
