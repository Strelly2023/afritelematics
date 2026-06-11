**AfriRide Postgres V1**
This document freezes the production data model for the authoritative AfriRide spine:

- `afriride_system`
- `AfriRideMobile`
- `dashboard`
- selected `afritech` replay/proof/runtime support

It translates the current SQLite-backed implementation into a PostgreSQL schema that preserves the core trust law:

`trace = authoritative execution record`

`replay`, `evidence`, and `receipt` remain deterministic derivations from trace.

**Schema Freeze V1**
Frozen entities:

- `Driver`
- `Ride`
- `RideEvent`
- `TraceEvent`
- `IdempotencyRecord`
- `ReplaySnapshot` as derived projection
- `EvidenceRecord` as derived projection
- `ReceiptRecord` as derived projection

Authoritative tables:

- `drivers`
- `rides`
- `ride_events`
- `trace_events`
- `idempotency_records`

Derived and disposable tables:

- `replay_snapshots`
- `evidence_records`
- `receipt_records`

Derived tables are allowed for export, caching, and operational inspection, but they are not truth-bearing. They may be truncated and rebuilt from `trace_events`.

**Design Rules**
1. `trace_events` is append-only.
2. Identity inside `trace_events` is server-attested, not client-declared.
3. Replay correctness depends on stable event ordering.
4. Receipt and evidence validity depend on reproducible trace hashing.
5. Any schema change affecting trace semantics is a compatibility event, not a routine migration.

**Important Ordering Decision**
Current repository behavior uses a global monotonic `sequence_id` for `trace_events`, not a ride-local counter. The Postgres v1 schema preserves that behavior.

Implications:

- the hash chain is global across the entire trace ledger
- replay for a single ride uses the ride's subset of trace events ordered by global `sequence_id`
- `trace_events.sequence_id` must remain unique across all trace events
- `trace_events(ride_id, sequence_id)` should be indexed for efficient ride replay

This is stricter than per-ride ordering and matches the current implementation in `TraceRepository.next_sequence_and_previous_hash()`.

**Frozen Entity Definitions**
`Driver`

- `driver_id`: stable actor identifier
- `online`: current availability flag
- operationally mutable
- not authoritative for proof

`Ride`

- `ride_id`: stable ride identifier
- `passenger_id`: authoritative rider identity for the ride
- `pickup`
- `destination`
- `status`
- `assigned_driver`
- `trace_hash`
- `state_hash`
- `events_json`

`Ride` is an operational projection. It is convenient state, not the final proof source.

`RideEvent`

- append-only ride lifecycle event log
- operational event stream used by the current backend
- subordinate to trace for proof purposes

`TraceEvent`

- `event_id`
- `sequence_id`
- `device_id`
- `actor_type`
- `actor_id`
- `action`
- `payload_json`
- `local_timestamp`
- `normalized_timestamp`
- `app_version`
- `test_mode`
- `ride_id`
- `transition`
- `previous_hash`
- `event_hash`

`TraceEvent` is the canonical execution ledger.

`IdempotencyRecord`

- `idempotency_key`
- `fingerprint`
- `result_json`

This is operational safety state. It is not proof state.

`ReplaySnapshot`

- deterministic reconstruction for a ride
- keyed by `ride_id`
- includes `trace_hash`, `replay_hash`, lifecycle state, and verification flag

`EvidenceRecord`

- derived replay validation result
- keyed by `ride_id`
- includes `verification_status`

`ReceiptRecord`

- derived proof artifact
- keyed by `receipt_id` and `ride_id`
- includes `receipt_hash`

**Authoritative Constraints**
`drivers`

- primary key on `driver_id`

`rides`

- primary key on `ride_id`
- `status` constrained to the canonical lifecycle set:
  - `REQUESTED`
  - `DRIVER_ASSIGNED`
  - `IN_TRIP`
  - `COMPLETED`
  - `CANCELED`
  - `REJECTED`
  - `UNKNOWN`

`ride_events`

- bigserial primary key for append order
- foreign key to `rides(ride_id)` with `ON DELETE CASCADE`

`trace_events`

- bigserial internal row id
- unique `event_id`
- unique `sequence_id`
- `actor_type` constrained to:
  - `rider`
  - `driver`
  - `operator`
- `previous_hash` nullable only for the genesis row
- `event_hash` unique
- foreign key to `rides(ride_id)` with `ON DELETE SET NULL`
- indexes on `ride_id`, `(ride_id, sequence_id)`, and `actor_id`

`idempotency_records`

- primary key on `idempotency_key`

**Derived Projection Constraints**
`replay_snapshots`

- one row per `ride_id`
- foreign key to `rides(ride_id)` with `ON DELETE CASCADE`
- `replay_verified` boolean

`evidence_records`

- one row per `ride_id`
- foreign key to `rides(ride_id)` with `ON DELETE CASCADE`
- `verification_status` constrained to:
  - `VERIFIED`
  - `REJECTED`

`receipt_records`

- primary key on `receipt_id`
- unique `ride_id`
- foreign key to `rides(ride_id)` with `ON DELETE CASCADE`

**Backward Compatibility Rules**
1. Existing event payload keys must remain readable after migration.
2. `trace_events.payload_json` remains schemaless `jsonb`, but semantic meaning of keys must not change silently.
3. `event_hash` and `previous_hash` formats must remain byte-for-byte stable for the same canonical input.
4. `sequence_id` ordering semantics must not change in v1.
5. Derived tables must never become the sole source for replay, evidence, or receipt APIs.

**SQLite To Postgres Migration Plan**
Phase 1. Schema deployment

- create Postgres schema from `scripts/sql/afriride_postgres_schema_v1.sql`
- keep SQLite as the active runtime store during validation

Phase 2. Data export from SQLite

- export `drivers`
- export `rides`
- export `ride_events`
- export `trace_events`
- export `idempotency_records`

Phase 3. Deterministic import

- import authoritative tables first
- preserve:
  - `trace_events.event_id`
  - `trace_events.sequence_id`
  - `trace_events.previous_hash`
  - `trace_events.event_hash`
- preserve `ride_events.event_id` ordering values if migrated

Phase 4. Replay audit

- run replay on a representative ride set from Postgres
- compare:
  - replay status
  - assigned driver
  - transitions
  - trace hash
  - replay hash
  - receipt hash

Phase 5. Derived projection rebuild

- regenerate:
  - `replay_snapshots`
  - `evidence_records`
  - `receipt_records`

Phase 6. Cutover

- switch repository adapters from SQLite to Postgres
- keep SQLite snapshot for rollback

**Migration Acceptance Criteria**
1. Trace row count matches exactly.
2. Every `event_id` survives unchanged.
3. Every `sequence_id` survives unchanged.
4. Every `event_hash` survives unchanged.
5. Replay output for sampled rides matches pre-migration output.
6. Receipt hashes for sampled rides match pre-migration output.
7. Authenticated identity semantics remain unchanged at the API layer.

**Operational Notes**
- `events_json` on `rides` is preserved in v1 to match the current application model, even though trace is the proof source.
- `ride_events` is preserved because the backend still uses it operationally.
- derived tables may be populated lazily or omitted at first deployment if the API continues deriving directly from trace.

**Non-Goals For V1**
- multi-region partitioning
- event version registry
- external signature verification
- device-level signing
- payment ledger integration

Those can be layered on later without changing the core trust law.
