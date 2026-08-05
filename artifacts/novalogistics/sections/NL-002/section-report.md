# NL-002 — Persistence, migrations, and transactional outbox

Certified baseline: `7731391776a65a18bbf58a72ceed3798ef0099af`

Branch: `feature/product-factory-enterprise-sdlc`

## Implementation

Added persistence-neutral repository contracts, query objects, and explicit errors; deterministic aggregate/event codecs (`afritech.novalogistics.persistence.v1`); forward-only SQLite migration execution; typed SQLite repository adapters for all NL-001 persisted types; version-conditional writes; tenant-scoped queries; and a transactional outbox.

Files added: `afritech/novalogistics/persistence.py`, `afritech/novalogistics/codec.py`, `afritech/novalogistics/sqlite.py`, `afritech/tests/novalogistics/test_persistence.py`, and NL-002 evidence. `afritech/novalogistics/__init__.py` was compatibly extended.

## Database contract

- Migration: `0001_novalogistics_aggregate_outbox`.
- Tables: `novalogistics_schema_migrations`, `novalogistics_aggregates`, `novalogistics_outbox`.
- Primary/composite keys isolate tenants and aggregate types.
- Tenant-scoped business-key uniqueness and outbox event/order uniqueness are enforced.
- Composite outbox-to-aggregate foreign key uses cascade cleanup.
- Indexes cover tenant/type/status/update ordering, tenant business keys, and deterministic pending-outbox retrieval.

## Safety strategies

- Concurrency: `BEGIN IMMEDIATE` plus conditional update on tenant/type/id/expected version; stale, absent, and cross-tenant writes have distinct public errors.
- Tenant isolation: every public read/write predicate requires tenant identity; business keys and outbox retrieval are tenant-scoped.
- Atomicity: aggregate state and event rows share one transaction and rollback together.
- Serialization: allow-listed type registry, stable JSON keys, enum strings, UTC ISO timestamps, explicit schema, no pickle or dynamic imports.
- PostgreSQL readiness: `SCHEMA_AND_CONTRACT_READY`; no untested PostgreSQL adapter or dependency is claimed.

## Validation

- Compile: PASS.
- Focused persistence: 16 passed.
- All NovaLogistics: 27 passed.
- Migration subset: 2 passed.
- Concurrency subset: 3 passed.
- Tenant subset: 4 passed.
- Outbox/rollback subset: 4 passed.
- Broader logistics compatibility: 66 passed.
- Shared persistence compatibility: 15 passed.
- Public web: 5 passed.
- Import topology: PASS.

Runtime-boundary, constitutional pipeline, unified validation, final diff checks, and commit are recorded during final staging. Known limitation: SQLite is the exercised adapter; PostgreSQL execution remains provider-pending.
