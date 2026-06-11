# AfriRide Phase 3 Live Operations And Monitoring Governance Spec

Status: PHASE 3 LIVE OPERATIONS AND MONITORING GOVERNANCE SPEC
Classification: LIVE_OPERATIONS_REPLAY_LINKED_MONITORING_GATE

Purpose: define the bounded governance contract for live operations,
monitoring, and replay-linked operational response after the cutover gate has
passed.

This specification is not live production success evidence.

This specification does not prove:

```text
global production readiness
mass-market reliability
all incidents automatically recover
all alerts are perfect
all operator actions are correct
```

It governs only this bounded claim:

```text
live operations remain replay-linked, trace-backed, and non-authoritative
```

## Preconditions

Phase 3 begins only after:

- cutover gate completed
- Postgres-backed runtime is the active governed target
- replay/evidence/receipt outputs remained stable across restart
- [`AFRIRIDE_PHASE2_MIGRATION_GOVERNANCE_SPEC.md`](/Users/ostrinov/afritelematics/docs/pilot/AFRIRIDE_PHASE2_MIGRATION_GOVERNANCE_SPEC.md) remained green
- [`BIND-001-phase1-phase2.yaml`](/Users/ostrinov/afritelematics/afritech/governance/bindings/BIND-001-phase1-phase2.yaml) remained valid

## Monitoring Rule

```text
observability explains trace-backed state
observability never overrides trace-backed state
```

## Phase 3 Execution Layer

Phase 3 evolves the system from migration-governed readiness into a bounded
live execution layer with four replay-linked operational surfaces:

```text
live monitoring dashboard (replay-backed)
operator alert rules (evidence-driven)
anomaly detection on trace chain
real-time replay verification
```

The execution rule is:

```text
live signal
-> trace lookup
-> replay verification
-> evidence-linked alert
-> bounded operator action
```

## Required Operational Views

- live `/health` status
- replay health summary
- evidence summary
- guard violation board
- trace lookup by `ride_id`
- cutover evidence archive
- device/token anomaly board

### Live Monitoring Dashboard (replay-backed)

The dashboard must remain replay-backed rather than inference-backed.

Required dashboard panels:

- live health and API reachability
- replay success rate
- replay divergence queue
- evidence verification status
- receipt stability board
- trace completeness board
- device/token exception board
- cutover gate history

Required dashboard linkage:

```text
every dashboard card links to ride_id or trace_id
every operational summary links to replay_hash or receipt_hash
every displayed anomaly links to raw trace evidence
```

## Required Alerts

- replay divergence alert
- trace completeness alert
- receipt instability alert
- token/auth anomaly alert
- cutover rollback alert
- operator override attempt alert

### Operator Alert Rules (evidence-driven)

Operator alerts must be evidence-driven rather than threshold-only.

Required alert rules:

- emit replay divergence alert only when replay output mismatches governed expectation
- emit trace completeness alert only when a trace gap or missing transition is evidenced
- emit receipt instability alert only when the same governed ride yields a changed receipt hash
- emit token/auth anomaly alert only when an auth event cannot be reconciled to actor_id, device_id, and trace evidence
- emit operator override attempt alert only when an attempted manual truth mutation is captured

Required alert payload:

```text
alert_id
alert_type
ride_id
trace_id
event_id
replay_hash
receipt_hash_optional
evidence_pointer
severity
opened_at
```

Operator action is admissible only when the alert payload is evidence-complete.

### Anomaly Detection On Trace Chain

Anomaly detection must operate on the trace chain itself, not on detached
dashboard summaries.

Required anomaly classes:

- sequence gap anomaly
- duplicate event anomaly
- invalid previous_hash anomaly
- actor/device identity drift anomaly
- impossible transition anomaly
- abnormal retry burst anomaly
- replay mismatch anomaly

Required anomaly discipline:

```text
anomaly detection may classify risk
anomaly detection may not redefine truth
anomaly detection output must remain trace-linked
anomaly suppression must be recorded
```

### Real-Time Replay Verification

Phase 3 requires real-time replay verification for high-value live mutations.

Real-time replay verification means:

```text
each governed live mutation enters trace
replay is re-run on the affected ride window
replay result is compared to expected derived state
verification result is attached to the live monitoring surface
```

Required real-time replay checks:

- ride request replay check
- driver accept replay check
- trip start replay check
- trip complete replay check
- receipt issuance replay check

Required outcomes:

```text
verification_status=VERIFIED when replay matches
verification_status=REJECTED when replay diverges
verification_latency remains observable
verification failure opens replay divergence alert
```

## Required Investigation Keys

Every live operations investigation must link back to:

```text
ride_id
trace_id
event_id
request_id
actor_id
device_id
replay_hash
receipt_hash
```

## Operator Boundaries

Operators may:

- inspect status
- inspect replay evidence
- inspect receipts
- isolate failing writes
- trigger rollback review
- acknowledge evidence-complete alerts
- request replay rerun through governed tooling

Operators may not:

- mutate truth from observability surfaces
- declare replay valid without replay evidence
- declare receipt valid without receipt evidence
- bypass trace-backed investigation
- promote dashboards into runtime authority

## Stop Conditions

Pause escalation and open incident review if any occur:

```text
replay divergence detected
trace completeness drops below target
receipt hash changes for same governed ride
auth anomaly cannot be traced
operator action is not trace-linked
observability surface becomes authoritative
```

## Evidence Preservation

Required preserved artifacts:

- health snapshots
- replay health exports
- evidence exports
- guard violation exports
- replay verification snapshots
- anomaly detection outputs
- alert payload exports
- incident timeline
- rollback notes
- alert-to-trace resolution notes

## Claim Discipline

Passing Phase 3 permits only:

```text
live operations are governed by replay-linked monitoring and bounded operator procedures
```

Passing Phase 3 does not permit:

```text
production proven
global launch approved
all scaling risks removed
all monitoring complete forever
```
