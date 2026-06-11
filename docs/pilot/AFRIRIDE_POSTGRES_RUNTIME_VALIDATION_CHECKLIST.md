# AfriRide Postgres Runtime Validation Checklist

Status: PRE-CUTOVER VALIDATION DOCUMENT

Purpose: validate that the new Postgres-backed runtime preserves the authoritative trust law:

```text
trace = authoritative ledger
replay/evidence/receipt = deterministic derivations
```

This checklist is complete only when live Postgres execution matches the current SQLite-backed spine with no replay or receipt divergence.

## Preconditions

- [`scripts/sql/afriride_postgres_schema_v1.sql`](/Users/ostrinov/afritelematics/scripts/sql/afriride_postgres_schema_v1.sql) exists and is unchanged from Schema Freeze V1.
- [`scripts/afriride_sqlite_to_postgres_migrate.py`](/Users/ostrinov/afritelematics/scripts/afriride_sqlite_to_postgres_migrate.py) exists.
- [`scripts/afriride_replay_diff_checker.py`](/Users/ostrinov/afritelematics/scripts/afriride_replay_diff_checker.py) exists.
- [`afriride_system/backend/storage.py`](/Users/ostrinov/afritelematics/afriride_system/backend/storage.py) supports both SQLite and Postgres.
- a known-good SQLite source database exists
- a clean Postgres target database exists
- `psycopg[binary]` is installed in the runtime environment

## Step 1. Environment Validation

- Confirm `AFRIRIDE_DATABASE_URL` points to the intended Postgres database.
- Confirm the database is reachable from the application environment.
- Confirm the application can import `psycopg`.
- Confirm the SQLite source file is the correct cutover candidate.

Pass condition:

- connection succeeds to both source and target

Stop condition:

- wrong database URL
- missing Postgres driver
- stale or wrong SQLite source

## Step 2. Schema Validation

- Apply [`afriride_postgres_schema_v1.sql`](/Users/ostrinov/afritelematics/scripts/sql/afriride_postgres_schema_v1.sql) to the target database.
- Confirm all required tables exist:
  - `drivers`
  - `rides`
  - `ride_events`
  - `trace_events`
  - `idempotency_records`
  - `replay_snapshots`
  - `evidence_records`
  - `receipt_records`
- Confirm key constraints exist:
  - `trace_events.event_id` unique
  - `trace_events.sequence_id` unique
  - `trace_events.event_hash` unique
  - `trace_events.actor_type` check constraint

Pass condition:

- schema created with no errors

Stop condition:

- any missing table
- any missing uniqueness or actor-type constraint

## Step 3. Migration Dry Run

Run:

```bash
python scripts/afriride_sqlite_to_postgres_migrate.py \
  --sqlite-path /path/to/pilot_state.sqlite3 \
  --postgres-url "$AFRIRIDE_DATABASE_URL" \
  --truncate-target \
  --verify
```

Validation goals:

- authoritative tables copy cleanly
- derived tables rebuild cleanly
- source and target ride sets match

Pass condition:

- migration exits `0`

Stop condition:

- migration exception
- schema mismatch
- determinism mismatch

## Step 4. Determinism Verification

Run:

```bash
python scripts/afriride_replay_diff_checker.py \
  --source /path/to/pilot_state.sqlite3 \
  --target "$AFRIRIDE_DATABASE_URL"
```

Pass condition:

- JSON output reports `"ok": true`
- ride count matches expected migrated rides

Stop condition:

- any ride mismatch in:
  - replay output
  - evidence output
  - receipt output

## Step 5. Runtime Boot Validation

Boot the application with:

```bash
AFRIRIDE_DATABASE_URL="$AFRIRIDE_DATABASE_URL" uvicorn afriride_system.api.main:app
```

Validate:

- `/auth/token` responds
- authenticated rider flow works
- authenticated driver flow works
- `/ride/{ride_id}/replay` responds
- `/ride/{ride_id}/evidence` responds
- `/ride/{ride_id}/receipt` responds

Pass condition:

- API boots and proof endpoints return valid responses

Stop condition:

- startup error
- repository/query failure
- trace write failure
- proof route mismatch

## Step 6. Write Path Validation

Create a fresh ride using the Postgres-backed runtime:

1. issue rider token
2. request ride
3. set driver online
4. accept ride
5. start ride
6. complete ride

Validate in Postgres:

- `rides` row exists
- `ride_events` rows exist
- `trace_events` rows exist
- `trace_events.sequence_id` ordering is monotonic
- `trace_events.previous_hash` chain is intact

Pass condition:

- new writes succeed and are replayable

Stop condition:

- missing trace row
- duplicate or broken sequence chain
- receipt/evidence failure for new ride

## Step 7. Derived Projection Rebuild Validation

After live writes, rerun derived rebuild by re-running migration with `--skip-derived-rebuild` disabled or by internal rebuild tooling once available.

Validate:

- `replay_snapshots` matches runtime replay output
- `evidence_records` matches runtime evidence output
- `receipt_records` matches runtime receipt output

Pass condition:

- derived projections are reproducible

Stop condition:

- derived table content differs from runtime derivation

## Step 8. Restart Durability Validation

Restart the Postgres-backed API process and recheck:

- ride status endpoint
- replay endpoint
- evidence endpoint
- receipt endpoint

Pass condition:

- results are identical before and after restart

Stop condition:

- any change in replay, evidence, or receipt output for the same ride

## Final Validation Gate

Postgres runtime validation passes only if all conditions are true:

- schema applied successfully
- migration succeeded
- replay diff checker reports no mismatches
- Postgres-backed runtime boots and serves authenticated flows
- new writes produce valid trace rows
- replay/evidence/receipt remain stable across restart

## Not Proven By This Checklist

This checklist does not prove:

- real driver behavior
- real rider behavior
- mobile token lifecycle correctness
- production traffic handling
- real-world recovery under incident pressure

Those belong to pilot rollout and field execution evidence.
