# AfriRide Phase 1 Setup Runbook

Status: SETUP RUNBOOK
Classification: OPERATOR AND ENGINEER EXECUTION SURFACE

Purpose: prepare a clean AfriRide execution environment where dependencies,
storage wiring, and API boot behavior are verified before runtime validation,
migration, or live pilot work begins.

This runbook is not runtime authority.

Governance chain:

```text
ADR -> INVARIANT -> BINDING -> RULE -> GUARD -> RUNNER -> PHASE 2 GATE
```

Phase 1 governed artifacts:

- [`RULE-001-phase1-runbook.yaml`](/Users/ostrinov/afritelematics/afritech/governance/rules/RULE-001-phase1-runbook.yaml)
- [`guard_phase1_runbook.py`](/Users/ostrinov/afritelematics/afritech/guards/guard_phase1_runbook.py)
- [`run_phase1_setup.sh`](/Users/ostrinov/afritelematics/scripts/run_phase1_setup.sh)

This runbook does not prove:

```text
determinism
replay correctness
receipt correctness
production readiness
pilot readiness
real-world safety
```

It proves only:

```text
execution environment ready
dependency integrity checked
persistence wiring reachable
API boot path operational
```

## Objective

Phase 1 is complete only when all of the following are true:

- dependencies are installed
- the Python runtime can import the required storage driver
- SQLite boots successfully
- Postgres boots successfully when configured
- schema application succeeds
- the storage adapter selects the intended backend
- the API can issue an auth token
- the basic ride request flow works

## 1. Environment Preparation

### 1.1 Enter the repository

```bash
cd /Users/ostrinov/afritelematics
```

### 1.2 Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python --version
```

Expected:

```text
Python 3.10+ recommended
Python 3.11 preferred
```

## 2. Dependency Installation

### 2.1 Install core requirements

```bash
pip install -r requirements.txt
```

### 2.2 Validate critical runtime dependencies

The Phase 1 spine depends on:

- FastAPI
- Uvicorn
- Pydantic
- `psycopg` for Postgres mode
- SQLite from the Python standard library

### 2.3 Verify `psycopg`

```bash
python - <<'PY'
import psycopg
print("psycopg OK")
PY
```

Fail condition:

```text
ModuleNotFoundError: psycopg
```

Fix:

```bash
pip install "psycopg[binary]"
```

### 2.4 Optional focused validation tests

Instead of claiming a fixed total test count, run the Phase 1-focused checks:

```bash
python3 -m pytest \
  afriride_system/tests/test_authentication.py \
  afriride_system/tests/test_api_flow.py \
  afriride_system/tests/test_persistence_durability.py
```

Pass condition:

```text
all selected Phase 1 tests pass
```

## 3. Database Configuration

The current spine supports dual storage modes:

```text
SQLite -> baseline and local reference
Postgres -> target runtime
```

### 3.1 SQLite setup

The API chooses SQLite when `AFRIRIDE_DATABASE_URL` is not set.

Optional explicit override:

```bash
export AFRIRIDE_DB_PATH="$PWD/data/afriride.sqlite3"
mkdir -p data
```

If no override is set, the default SQLite file is:

```text
afriride_system/pilot_state.sqlite3
```

### 3.2 PostgreSQL setup

Create the target database:

```bash
psql postgres
```

Then:

```sql
CREATE DATABASE afriride;
```

Set the runtime connection URL:

```bash
export AFRIRIDE_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/afriride"
```

Validate connectivity:

```bash
psql "$AFRIRIDE_DATABASE_URL" -c '\conninfo'
```

Pass condition:

```text
connection succeeds to the intended afriride database
```

Fail conditions:

```text
connection refused
authentication failed
wrong target database
```

## 4. Apply Schema for Postgres Mode

Required file:

[`scripts/sql/afriride_postgres_schema_v1.sql`](/Users/ostrinov/afritelematics/scripts/sql/afriride_postgres_schema_v1.sql)

Apply the schema:

```bash
psql "$AFRIRIDE_DATABASE_URL" \
  -f scripts/sql/afriride_postgres_schema_v1.sql
```

Verify the required tables:

```bash
psql "$AFRIRIDE_DATABASE_URL" -c "\dt"
```

Expected tables:

```text
drivers
rides
ride_events
trace_events
idempotency_records
replay_snapshots
evidence_records
receipt_records
```

Verify key constraints:

```bash
psql "$AFRIRIDE_DATABASE_URL" -c "
SELECT indexdef
FROM pg_indexes
WHERE tablename = 'trace_events';
"
```

The result must include unique indexes for:

- `event_id`
- `sequence_id`
- `event_hash`

## 5. Storage Adapter Verification

Authoritative file:

[`afriride_system/backend/storage.py`](/Users/ostrinov/afritelematics/afriride_system/backend/storage.py)

Gateway selection path:

[`afriride_system/api/dispatcher_adapter.py`](/Users/ostrinov/afritelematics/afriride_system/api/dispatcher_adapter.py)

Expected selection behavior:

| Condition | Backend |
| --- | --- |
| `AFRIRIDE_DATABASE_URL` unset | SQLite |
| `AFRIRIDE_DATABASE_URL` set to `postgres://` or `postgresql://` | Postgres |

### 5.1 Verify SQLite mode

```bash
unset AFRIRIDE_DATABASE_URL
uvicorn afriride_system.api.main:app
```

### 5.2 Verify Postgres mode

```bash
export AFRIRIDE_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/afriride"
uvicorn afriride_system.api.main:app
```

Pass condition:

```text
app boots successfully
no schema or connection errors occur
API responds to HTTP requests
```

Fail conditions:

```text
connection error
missing schema
psycopg import error
backend selection mismatch
```

## 6. API Boot Validation

Start the server:

```bash
uvicorn afriride_system.api.main:app --reload
```

### 6.1 Check root health

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{
  "status": "ok",
  "service": "afriride-api"
}
```

### 6.2 Check OpenAPI docs

```bash
curl -I http://127.0.0.1:8000/docs
```

Pass condition:

```text
HTTP 200 returned for the docs surface
```

### 6.3 Check token issuance

```bash
curl -X POST http://127.0.0.1:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id":"setup-rider","role":"RIDER"}'
```

Expected shape:

```json
{
  "token": "..."
}
```

## 7. Minimal Functional Check

### 7.1 Issue a rider token

```bash
export TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id":"setup-rider","role":"RIDER"}' | jq -r .token)
```

### 7.2 Request a ride

```bash
curl -X POST http://127.0.0.1:8000/passenger/request-ride \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: setup-request-1" \
  -d '{
    "passenger_id":"setup-rider",
    "pickup":"A",
    "destination":"B",
    "ride_id":"setup-test-1"
  }'
```

Expected response shape:

```json
{
  "status": "success",
  "data": {
    "ride_id": "setup-test-1",
    "status": "REQUESTED"
  },
  "error": null
}
```

Pass condition:

```text
request accepted
response status is success
ride state is REQUESTED
```

## 8. Completion Criteria

Phase 1 Setup is complete only when:

```text
dependencies installed
psycopg import validated
SQLite runtime boot validated
Postgres runtime boot validated
schema applied successfully
storage adapter selection validated
API boot validated
auth token issuance validated
basic ride request flow validated
```

## 9. Stop Conditions

Stop and fix the environment if any of the following occur:

```text
wrong database URL
schema missing or partially applied
psycopg missing in Postgres mode
API fails to boot
auth endpoint fails
ride request flow fails
storage adapter routes to the wrong backend
```

## 10. What Phase 1 Achieves

Phase 1 establishes:

```text
execution environment
dependency integrity
persistence wiring
bootable API surface
```

It does not establish:

```text
deterministic replay proof
evidence correctness proof
receipt correctness proof
pilot readiness
```

## 11. What Comes Next

After Phase 1 Setup, continue with:

- [`AFRIRIDE_POSTGRES_RUNTIME_VALIDATION_CHECKLIST.md`](/Users/ostrinov/afritelematics/docs/pilot/AFRIRIDE_POSTGRES_RUNTIME_VALIDATION_CHECKLIST.md)
- [`AFRIRIDE_POSTGRES_CUTOVER_RUNBOOK.md`](/Users/ostrinov/afritelematics/docs/pilot/AFRIRIDE_POSTGRES_CUTOVER_RUNBOOK.md)
- [`AFRIRIDE_PHASE2_MIGRATION_GOVERNANCE_SPEC.md`](/Users/ostrinov/afritelematics/docs/pilot/AFRIRIDE_PHASE2_MIGRATION_GOVERNANCE_SPEC.md)
- [`AFRIRIDE_FIRST_PILOT_ROLLOUT_PLAN.md`](/Users/ostrinov/afritelematics/docs/pilot/AFRIRIDE_FIRST_PILOT_ROLLOUT_PLAN.md)
