# NovaID PostgreSQL Production Authority Certificate

## Decision

**PASS — PostgreSQL is the sole admissible NovaID production persistence
authority for the certified scope.**

The certification ran on PostgreSQL 16.14 in an isolated local container.
The server reported that it was the writable primary (`pg_is_in_recovery() =
false`). SQLite was explicitly rejected by the production runtime gate.

## Certified controls

| Control | Result | Evidence |
|---|---:|---|
| Production backend authority | PASS | Production rejects SQLite and accepts a valid PostgreSQL configuration |
| Clean database bootstrap | PASS | 10 ordered revisions, 43 tables, 586 constraints |
| Migration integrity | PASS | SHA-256 recorded for every applied revision |
| Migration serialization | PASS | PostgreSQL transaction-scoped advisory lock |
| Failed migration rollback | PASS | Injected DDL failure left neither partial table nor partial ledger |
| Concurrent workload | PASS | 1,200 transactions, 12 workers, 12 tenants, 300 identities |
| Write integrity | PASS | 1,200 version increments and 1,200 audit events; zero lost writes |
| Tenant integrity | PASS | Zero cross-tenant integrity violations |
| Repository integration | PASS | PostgreSQL UoW integration and 20-iteration races passed |

## Measured workload

- Throughput: **316.23 transactions/second**
- Median latency: **34.345 ms**
- p95 latency: **67.273 ms**
- p99 latency: **84.771 ms**
- Maximum latency: **124.849 ms**
- Total elapsed time: **3.795 seconds**

Every workload transaction acquired a row lock, performed a tenant-bound
identity version update, wrote a security audit event, and committed. Final
database reconciliation proved that committed version increments and audit
events both equalled the requested operation count.

## Migration and rollback architecture

The canonical migration runner:

1. obtains a PostgreSQL advisory transaction lock;
2. verifies the ordered migration inventory;
3. validates SHA-256 checksums for previously applied revisions;
4. applies all pending revisions inside one transaction;
5. records each revision and checksum in the migration ledger; and
6. rolls back the entire chain on any failure.

Rollback validation injected a valid table creation followed by invalid DDL.
PostgreSQL aborted the migration transaction. Subsequent inspection confirmed
that both the table and migration ledger were absent.

## Defects closed during certification

- Revision `0009` now records its migration-ledger entry.
- Revision `0010` now uses UUID foreign keys compatible with the authoritative
  tenant and membership primary keys.
- Migration-owned `BEGIN`/`COMMIT` statements were removed so the runner owns
  atomic rollback.
- The PostgreSQL unit of work now exposes the registration idempotency,
  tenant-status, membership, and challenge operations required by the
  production authentication service.

## Reproduction

```bash
python scripts/novaid/certify_postgres_production.py \
  --dsn "$NOVAID_TEST_DATABASE_URL" \
  --output artifacts/novaid/production-database-certification/postgresql-production-certification.json \
  --workers 12 \
  --operations 1200 \
  --tenants 12 \
  --identities-per-tenant 25
```

Machine-readable evidence:
`postgresql-production-certification.json`

Evidence SHA-256:
`753ee29f169f520fc1678531c917887669520e97b2b1503568511f0112a6be27`

## Scope boundary

This certificate demonstrates application correctness, migration atomicity,
rollback behavior, concurrency integrity, and local primary-database workload
performance. It does **not** claim managed-service failover, point-in-time
recovery, replica promotion, network partition tolerance, multi-region
latency, backup restoration, or production capacity at forecast peak load.
Those controls require certification in the target production infrastructure.
