# NL-002 persistence discovery

Baseline: `7731391776a65a18bbf58a72ceed3798ef0099af` on `feature/product-factory-enterprise-sdlc`.

## Canonical patterns reused

- `afritech.core.infrastructure.persistence.event_store`: explicit expected-version conflicts.
- `afritech.novaride_runtime.persistence.postgres`: tenant-first repository APIs and conditional updates.
- `afritech.novaride_runtime.events`: aggregate-versioned event envelopes and ordered outbox retrieval.
- `afritech.novaid.persistence`: SQLite schema/migration separation and PostgreSQL boundary interfaces.
- `afritech.novacodepro.platform`: parameterized SQLite outbox operations.
- Repository-wide conventions: UTC ISO-8601 timestamps, JSON with sorted keys, foreign-key enforcement, and explicit transaction boundaries.

## Section design

- Domain-neutral repository errors, query values, and typed repository protocols live in `afritech.novalogistics.persistence` and do not import database drivers.
- Deterministic allow-listed codecs live in `afritech.novalogistics.codec`; pickle and arbitrary type loading are forbidden.
- SQLite migrations and repositories live in `afritech.novalogistics.sqlite`.
- One normalized aggregate table stores tenant, type, identifier, version, status, business key, timestamps, and deterministic payload.
- One outbox table stores deterministic event identity, tenant/aggregate identity, aggregate version, event type, immutable JSON payload/metadata, occurrence time, correlation/request identifiers, publish state, attempts, and bounded last error.
- Migration history is forward-only, ordered, transactional, and repeat-safe.

## Tables and indexes

- `novalogistics_schema_migrations`: migration id and applied UTC timestamp.
- `novalogistics_aggregates`: composite primary key `(tenant_id, aggregate_type, aggregate_id)` and tenant-scoped unique business key.
- `novalogistics_outbox`: primary key event id and composite foreign key to aggregate identity.
- Tenant/type/status/update, tenant/business-key, and pending-outbox deterministic-order indexes.

## Concurrency and atomicity

SQLite uses explicit `BEGIN IMMEDIATE`. Updates use tenant/type/id/version in the conditional predicate. A zero-row update distinguishes not-found, tenant mismatch, and stale-version conditions. Aggregate payload and new outbox rows are written before one commit; any error rolls back both.

## PostgreSQL readiness

The repository protocol, codec, normalized columns, composite keys, constraints, and parameter-neutral query model are PostgreSQL-ready. NL-002 does not add an untested PostgreSQL driver implementation; classification is `SCHEMA_AND_CONTRACT_READY`.

## Risks and exclusions

- SQLite serializes writers; higher-throughput PostgreSQL execution remains a later adapter implementation.
- Child histories remain inside their owning aggregate payload until domain ownership is expanded.
- Existing NovaPay receipt files, architecture work, administration work, NovaRide artifacts, local databases, caches, and recovery artifacts are explicitly excluded from staging.
