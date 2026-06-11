# AfriRide Phase 2 Migration Governance Spec

Status: PHASE 2 MIGRATION GOVERNANCE SPEC
Classification: SQLITE_TO_POSTGRES_EQUIVALENCE_GATE

Purpose: define the bounded governance contract for migrating AfriRide from the
SQLite-backed reference runtime to the Postgres-backed target runtime without
breaking the authoritative trust law:

```text
trace = authoritative ledger
replay/evidence/receipt = deterministic derivations
```

This specification is not migration success evidence.

This specification does not prove:

```text
production readiness
public pilot readiness
real-world safety
distributed fault tolerance
high concurrency correctness
```

It governs only one claim:

```text
migration must preserve replay, evidence, and receipt equivalence
```

## Governance Objective

Phase 2 exists to convert storage backends without creating a second truth
surface.

The migration path is admissible only when:

```text
SQLite source remains the current authority before cutover
Postgres target matches SQLite after migration
replay diff must report "ok": true
runtime boot must succeed against Postgres
restart stability must preserve replay/evidence/receipt outputs
```

## Inputs Under Governance

Governed artifacts:

- [`scripts/sql/afriride_postgres_schema_v1.sql`](/Users/ostrinov/afritelematics/scripts/sql/afriride_postgres_schema_v1.sql)
- [`scripts/afriride_sqlite_to_postgres_migrate.py`](/Users/ostrinov/afritelematics/scripts/afriride_sqlite_to_postgres_migrate.py)
- [`scripts/afriride_replay_diff_checker.py`](/Users/ostrinov/afritelematics/scripts/afriride_replay_diff_checker.py)
- [`scripts/afriride_postgres_cutover_runbook.sh`](/Users/ostrinov/afritelematics/scripts/afriride_postgres_cutover_runbook.sh)
- [`scripts/run_cutover_gate.sh`](/Users/ostrinov/afritelematics/scripts/run_cutover_gate.sh)
- [`docs/pilot/AFRIRIDE_POSTGRES_RUNTIME_VALIDATION_CHECKLIST.md`](/Users/ostrinov/afritelematics/docs/pilot/AFRIRIDE_POSTGRES_RUNTIME_VALIDATION_CHECKLIST.md)
- [`docs/pilot/AFRIRIDE_POSTGRES_CUTOVER_RUNBOOK.md`](/Users/ostrinov/afritelematics/docs/pilot/AFRIRIDE_POSTGRES_CUTOVER_RUNBOOK.md)
- [`BIND-001-phase1-phase2.yaml`](/Users/ostrinov/afritelematics/afritech/governance/bindings/BIND-001-phase1-phase2.yaml)

## Preconditions

Migration work must not begin until Phase 1 setup is governed and green:

- [`AFRIRIDE_PHASE1_SETUP_RUNBOOK.md`](/Users/ostrinov/afritelematics/docs/pilot/AFRIRIDE_PHASE1_SETUP_RUNBOOK.md) is current
- [`RULE-001-phase1-runbook.yaml`](/Users/ostrinov/afritelematics/afritech/governance/rules/RULE-001-phase1-runbook.yaml) is active
- `python3 -m afritech.guards.guard_phase1_runbook` passes
- the SQLite source file is identified and frozen for migration input
- the Postgres target database is clean and reachable

## Required Migration Gates

### Gate 1. Schema integrity

Required outcome:

```text
schema apply succeeds
required tables exist
trace uniqueness constraints exist
actor_type constraint exists
```

### Gate 2. Migration exit status

Required outcome:

```text
migration script exits 0
authoritative tables copy cleanly
derived tables rebuild cleanly
```

### Gate 3. Replay equivalence

Required outcome:

```text
replay diff must report "ok": true
ride count matches source
no replay mismatch
no evidence mismatch
no receipt mismatch
```

### Gate 4. Runtime boot

Required outcome:

```text
Postgres-backed API boots
/health returns 200
/auth/token returns 200
basic ride mutation succeeds
```

### Gate 5. Restart stability

Required outcome:

```text
replay output remains stable across restart
evidence output remains stable across restart
receipt output remains stable across restart
```

## Stop Conditions

Abort migration governance if any of the following occur:

```text
wrong source database selected
wrong target database selected
schema partially applied
migration exits non-zero
replay diff fails
Postgres runtime boots with mismatched behavior
restart changes replay/evidence/receipt outputs
```

## Claim Discipline

Passing Phase 2 permits only:

```text
SQLite-to-Postgres equivalence validated for the governed source set
```

Passing Phase 2 does not permit:

```text
production validated
pilot validated
global readiness achieved
all future migrations safe
all future schemas admissible
```

## Recommended Enforcement Chain

```text
Phase 1 Runbook
-> RULE-001
-> BIND-001
-> guard_phase1_runbook
-> guard_phase2_migration
-> runtime validation checklist
-> replay diff
-> run_cutover_gate.sh
-> cutover runbook
-> bounded migration claim
```

## What Comes Next

After the cutover gate is green, continue with:

- [`AFRIRIDE_PHASE3_LIVE_OPERATIONS_MONITORING_GOVERNANCE_SPEC.md`](/Users/ostrinov/afritelematics/docs/pilot/AFRIRIDE_PHASE3_LIVE_OPERATIONS_MONITORING_GOVERNANCE_SPEC.md)
