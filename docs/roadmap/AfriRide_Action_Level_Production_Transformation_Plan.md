# AfriRide - Action-Level Production Transformation Plan

## Document Classification

```text
STATUS: ACTION-LEVEL PRODUCTION HARDENING ROADMAP
CLASSIFICATION: ISOLATED OPERATIONAL ROADMAP SURFACE
GOVERNANCE MODE: PRESERVE OR ISOLATE
```

This plan defines practical execution steps for moving AfriRide from:

```text
GA Elite bounded correctness
```

toward:

```text
production-grade operational readiness
```

without weakening:

```text
deterministic execution
replay admissibility
constitutional boundaries
closed-world enforcement
claim discipline
```

This document is not runtime authority, replay authority, proof authority, and not evidence of production deployment.

It does not redefine:

```text
constitutional truth
replay authority
execution legality
core invariants
identity ontology
claim admissibility
operational deployment proof
```

---

# 1. First Principle

AfriRide production hardening must follow this rule:

```text
Do not scale the truth engine directly.
Scale controlled access to the truth engine.
```

The system must preserve the distinction between:

```text
deterministic core truth
```

and:

```text
adaptive production access
```

Production infrastructure may absorb real-world disorder. The AfriTech core must remain deterministic, replayable, invariant-bound, and constitutionally governed.

---

# 2. Split the System into Two Worlds

## World A - Truth Engine

The Truth Engine is the existing AfriTech constitutional core.

It remains:

```text
deterministic
replayable
invariant-bound
closed-world
constitutionally governed
```

Production hardening must not mutate this core to satisfy operational convenience.

## World B - Production System

The Production System is the new operational access layer.

It contains:

```text
APIs
queues
workers
mobile requests
maps adapters
payments adapters
scaling infrastructure
observability
```

This layer is allowed to be adaptive, but only through declared adapters, deterministic normalization, recorded external inputs, replay-safe queues, and bounded operational contracts.

## Final Separation

```text
Production System
-> Adapter and Control Layer
-> AfriTech Core
```

Core rule:

```text
Production is controlled adaptation.
Core is preserved truth.
```

---

# 3. Minimal Production Kernel

The first deployable AfriRide system should be intentionally small.

## MVP Architecture

```text
1 API service
1 queue
1 worker
1 event store
1 read database
```

## Candidate Stack

```text
API: Django, FastAPI, or Node
Queue: AWS SQS, Kafka, NATS, or Redis Streams
Workers: Python workers
State DB: PostgreSQL
Event Store: append-only event_log table
Read DB: PostgreSQL read model or Redis-backed materialized view
```

## Minimal Flow

```text
User request
-> API
-> Queue
-> Worker
-> AfriTech Core
-> Event Store
-> Read Database
-> Response
```

## Worker Authority Rule

```text
Worker is the only production component allowed to call the AfriTech core.
```

APIs, mobile apps, dashboards, notifications, maps, and payment providers must not call the core directly.

---

# 4. Replay Ledger

AfriRide already has replay semantics. Production hardening must make replay operationally durable.

Every operationally significant action must generate a replay ledger record.

## Required Ledger Fields

```json
{
  "event_id": "evt_001",
  "operation": "ride_requested",
  "input": {},
  "normalized_input": {},
  "output": {},
  "trace": {},
  "replay_hash": "hash",
  "timestamp": "recorded_observation_time",
  "sequence_id": 1,
  "partition_id": "city_melbourne"
}
```

## Storage Target

```text
event_log table
```

## Ledger Responsibilities

The replay ledger supports:

```text
audit trail
debugging
compliance evidence
rollback analysis
replay validation
continuity recovery
```

The ledger is operational evidence. It does not replace constitutional proof authority.

---

# 5. Controlled Handling of Real-World Mess

Real-world inputs are often:

```text
inconsistent
delayed
duplicated
unordered
noisy
provider-dependent
```

AfriRide must not pass this disorder directly into the AfriTech core.

## Normalization Flow

```text
External Input
-> Normalize
-> Canonical Input
-> Queue
-> Worker
-> Core
```

## GPS Example

External input:

```text
GPS latitude
GPS longitude
device timestamp drift
location jitter
network delay
```

Normalized input:

```text
canonical grid point
canonical sequence_id
recorded observation timestamp
source adapter version
replay-safe payload hash
```

## Normalization Rule

```text
Do not eliminate real-world noise by pretending it is clean.
Convert real-world noise into deterministic input.
```

---

# 6. Scaling Without Breaking Determinism

Scaling introduces:

```text
concurrency
race conditions
unordered messages
duplicate delivery
partial failure
```

AfriRide must scale through deterministic ordering and partitioned execution.

## Event Ordering Layer

Before core execution:

```text
events
-> validate
-> deduplicate
-> order
-> execute
```

## Partitioning

Use partition keys such as:

```text
city_id
trip_id
region_id
```

Recommended initial partition:

```text
partition_key = city_id
```

## Worker Groups

Each partition should have:

```text
own queue
own worker group
own ordering constraints
own dead-letter queue
own replay recovery boundary
```

## Scaling Result

This model supports:

```text
horizontal scaling
deterministic execution
failure isolation
replay-safe recovery
```

---

# 7. External Integrations via Recorded Inputs

External systems are non-deterministic and must not become hidden runtime truth.

Examples:

```text
Google Maps
Mapbox
OpenStreetMap
Stripe
M-Pesa
Flutterwave
Paystack
notification providers
traffic services
```

## Record and Replay Pattern

Instead of treating an external provider as a live replay dependency:

```text
call provider
-> store response
-> normalize response
-> execute using recorded response
```

During replay:

```text
use stored provider response
```

## Integration Rule

```text
External systems are input streams, not constitutional dependencies.
```

## Required Adapter Contracts

```text
maps_adapter_v1
payments_adapter_v1
gps_adapter_v1
notification_adapter_v1
identity_adapter_v1
```

Each adapter must declare:

```text
version
input schema
normalization rules
recorded response schema
failure behavior
replay behavior
idempotency requirements
```

---

# 8. Real Product Layer

After the minimal production kernel is stable, AfriRide can expand product capabilities.

## Required Modules

```text
deterministic matching engine
trip lifecycle orchestration
pricing engine
notification service
payment coordination service
driver availability service
rider request service
admin operations console
```

## Matching Engine

The matching engine must preserve:

```text
deterministic driver selection
explicit driver identity
replay-compatible assignment
recorded external inputs
```

## Trip Lifecycle

The lifecycle remains:

```text
REQUESTED
MATCHED
ACCEPTED
STARTED
COMPLETED
CANCELLED
FAILED
```

Lifecycle changes must be queue-mediated, ledger-recorded, and replay-validatable.

## Pricing

Pricing may be computed internally or sourced externally, but externally supplied pricing must be recorded before execution.

## Notifications

Notifications remain:

```text
async
observational
non-authoritative
failure-isolated
```

Notification failure must not mutate authoritative ride truth.

---

# 9. UI and UX Model

The frontend must not treat immediate UI state as truth.

## UI Rules

```text
submit intent
show pending state
poll or subscribe to confirmed state
render replay-confirmed result
handle delayed confirmation gracefully
```

The frontend may show:

```text
processing
request received
driver matching
confirmed
failed
retry available
```

but authoritative state comes from confirmed materialized state derived from the event log.

## Layer Trade-Off Model

| Layer | Behavior |
| --- | --- |
| Core | strict and deterministic |
| Edge | controlled and adaptive |
| UX | eventual and responsive |

---

# 10. Performance Optimization

Replay and validation can be expensive. Production hardening must optimize without replacing truth.

## Snapshots

```text
event log
-> snapshot
-> replay delta
```

Snapshot requirements:

```text
bind to event offset
include replay hash
include schema version
remain rebuildable from events
never replace source events
```

## Read Models

Separate:

```text
truth: event log
fast reads: materialized views and caches
```

Read models are:

```text
rebuildable
non-authoritative over replay
optimized for UX
safe to invalidate
```

## Async UX

The user experience should support:

```text
processing indicators
eventual confirmation
retryable failures
status polling
push updates
```

---

# 11. Deployment Strategy

AfriRide should deploy progressively.

## Phase A - Local Production Pilot

```text
1 city
100 users
single queue partition
single worker group
manual operations oversight
```

Goal:

```text
validate real behavior without claiming broad readiness
```

## Phase B - Controlled Regional Rollout

```text
1 region
1,000 users
multiple partitions
observability dashboards
basic incident runbooks
payment sandbox or limited live payments
```

## Phase C - Multi-Region Expansion

```text
regional partitions
regional queues
regional worker pools
regional failover policy
replay-compatible data boundaries
```

## Phase D - Scale Optimization

```text
add workers
add queues
optimize snapshots
optimize read models
expand adapter coverage
load-test partition behavior
```

---

# 12. Action-Level Roadmap

## Step 1 - Add Adapter Layer

Deliverables:

```text
adapter package
adapter contract schema
adapter version registry
normalization tests
recorded-input tests
```

## Step 2 - Introduce Queue-Based Execution

Deliverables:

```text
event queue
worker process
idempotency keys
deduplication logic
dead-letter queue
ordering tests
```

## Step 3 - Add Replay Ledger

Deliverables:

```text
event_log table
ledger schema
trace storage
replay_hash storage
partition_id storage
ledger migration
ledger tests
```

## Step 4 - Normalize External Inputs

Deliverables:

```text
GPS normalization
request normalization
provider response normalization
schema validation
canonical sequence assignment
```

## Step 5 - Partition Execution

Deliverables:

```text
city_id partitioning
trip_id ordering
partition worker assignment
partition replay boundary
failure isolation tests
```

## Step 6 - Scale Workers

Deliverables:

```text
stateless workers
worker concurrency limits
worker health checks
worker metrics
replay-safe retry policy
```

## Step 7 - Integrate External Systems via Recording

Deliverables:

```text
maps adapter
payment adapter
notification adapter
recorded provider response table
provider replay tests
adapter failure tests
```

## Step 8 - Build Product Features

Deliverables:

```text
rider booking flow
driver acceptance flow
trip lifecycle flow
admin operations flow
payment authorization flow
notification flow
support and incident flow
```

---

# 13. Validation Gates

Every production-hardening phase must pass:

```bash
python3 -m afritech.ci.constitutional_pipeline
python3 -m afritech.ci.claim_discipline_validator
python3 -m afritech.verify.replay
python3 -m afritech.demo.proof
pytest -q
```

Additional production tests:

```text
adapter contract tests
event schema compatibility tests
queue ordering tests
idempotency tests
snapshot replay tests
recorded input replay tests
load tests
security scans
rollback tests
incident runbook drills
```

---

# 14. Forbidden Production Claims

This roadmap must not be interpreted as evidence that AfriRide has achieved:

```text
production deployment readiness
global marketplace readiness
universal fault tolerance
complete state-space exhaustiveness
infinite-scale dispatch guarantees
multi-region commercial readiness
provider compliance completion
```

Those claims require additional operational evidence.

---

# 15. Safe Final Classification

```text
AfriRide action-level production transformation is a bounded roadmap
for scaling controlled access to a deterministic constitutional core
through adapters, queues, recorded inputs, replay ledgers, workers,
and materialized read models without redefining AfriTech truth,
replay authority, or operational deployment proof.
```
