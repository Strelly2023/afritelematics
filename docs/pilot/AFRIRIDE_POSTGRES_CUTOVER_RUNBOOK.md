# AfriRide Postgres Cutover Runbook

Status: CUTOVER EXECUTION RUNBOOK

Purpose: move the authoritative AfriRide spine from SQLite-backed runtime to Postgres-backed runtime without violating replay or receipt determinism.

## Scope

In scope:

- schema apply
- authoritative data migration
- derived projection rebuild
- replay diff verification
- runtime cutover
- rollback

Out of scope:

- mobile app release
- external secret rotation
- public launch

## Roles

- `Cutover Lead`: owns go/no-go decision
- `Database Operator`: runs schema and migration
- `Application Operator`: boots Postgres-backed API
- `Verifier`: runs replay diff checker and confirms invariants
- `Observer`: records timestamps and outcomes

## Required Inputs

- source SQLite file
- target Postgres database
- schema file:
  - [`afriride_postgres_schema_v1.sql`](/Users/ostrinov/afritelematics/scripts/sql/afriride_postgres_schema_v1.sql)
- migration tool:
  - [`afriride_sqlite_to_postgres_migrate.py`](/Users/ostrinov/afritelematics/scripts/afriride_sqlite_to_postgres_migrate.py)
- validation tool:
  - [`afriride_replay_diff_checker.py`](/Users/ostrinov/afritelematics/scripts/afriride_replay_diff_checker.py)

## T-1 Preparation

- freeze non-essential writes to the SQLite-backed environment
- confirm source DB snapshot path
- confirm target Postgres database is empty or approved for truncation
- confirm environment variable:
  - `AFRIRIDE_DATABASE_URL`
- confirm operator access to logs and API health endpoints

Go condition:

- all operators acknowledge correct source and target

## Step 1. Snapshot Source

- stop write traffic or place service in maintenance mode
- copy SQLite source file to a timestamped backup

Record:

- snapshot file path
- snapshot timestamp

Stop condition:

- source snapshot cannot be taken

## Step 2. Apply Postgres Schema

- execute Schema Freeze V1 DDL on target Postgres

Verify:

- all expected tables exist
- constraints exist on `trace_events`

Stop condition:

- schema apply failure

## Step 3. Run Migration

Run:

```bash
python scripts/afriride_sqlite_to_postgres_migrate.py \
  --sqlite-path /path/to/pilot_state.sqlite3 \
  --postgres-url "$AFRIRIDE_DATABASE_URL" \
  --truncate-target \
  --verify
```

Expected behavior:

- authoritative rows copied
- derived tables rebuilt
- internal source/target verification passes

Stop condition:

- non-zero exit

## Step 4. Independent Replay Diff

Run:

```bash
python scripts/afriride_replay_diff_checker.py \
  --source /path/to/pilot_state.sqlite3 \
  --target "$AFRIRIDE_DATABASE_URL"
```

Go condition:

- output shows `"ok": true`

Stop condition:

- any replay/evidence/receipt mismatch

## Step 5. Boot Postgres-Backed Runtime

Start API with:

```bash
AFRIRIDE_DATABASE_URL="$AFRIRIDE_DATABASE_URL" uvicorn afriride_system.api.main:app
```

Verify:

- app starts without storage errors
- `/auth/token` works
- authenticated read endpoints work
- proof endpoints return stable values for migrated rides

Stop condition:

- startup failure
- auth failure
- proof route failure

## Step 6. Live Write Smoke Test

Using the Postgres-backed runtime:

1. create rider token
2. create driver token
3. set driver online
4. request ride
5. accept ride
6. start ride
7. complete ride

Verify:

- trace rows written
- replay succeeds
- evidence returns `VERIFIED`
- receipt returns stable hash

Stop condition:

- any write path or proof derivation failure

## Step 7. Go/No-Go Decision

Go only if all are true:

- migration succeeded
- replay diff checker clean
- Postgres runtime booted
- live write smoke test passed

No-go if any fail.

## Rollback Plan

Rollback triggers:

- migration mismatch
- replay mismatch
- API instability
- live write failure

Rollback steps:

1. stop Postgres-backed runtime
2. restore SQLite-backed runtime using frozen snapshot
3. point runtime back to SQLite path
4. confirm pre-cutover replay/evidence/receipt outputs
5. record rollback reason and mismatch evidence

Rollback success condition:

- original SQLite-backed service resumes with matching proof outputs

## Cutover Evidence To Preserve

- schema apply logs
- migration tool output
- replay diff checker JSON
- API boot logs
- smoke test results
- rollback notes if triggered

These artifacts should be stored as cutover evidence, not just console output.
