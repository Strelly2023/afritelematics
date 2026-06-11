# AFRIRIDE_PILOT_EXECUTION_PLAN

## Status

Execution plan for moving the authoritative AfriRide production spine from architectural clarity to operational durability.

This plan applies only to the production spine declared in:

- [`AFRIRIDE_PRODUCTION_SPINE.md`](../architecture/AFRIRIDE_PRODUCTION_SPINE.md)
- [`AFRIRIDE_PILOT_READINESS.md`](./AFRIRIDE_PILOT_READINESS.md)

## Objective

Advance AfriRide from:

```text
architecture authority established
```

to:

```text
operationally durable controlled pilot
```

## Guiding Rule

Every task in this plan must strengthen the production spine and must not create another competing spine.

## Current Blockers

The current pilot blockers are:

1. persistence
2. authentication
3. evidence durability
4. dashboard contract alignment

These are ordered deliberately.
Persistence comes first because replay, receipts, and evidence authority all depend on durable state.

## Phase 1: Persistence

### Goal

No ride state or driver state is lost on restart.

Execution setup for this phase is defined in:

- [`AFRIRIDE_PHASE1_SETUP_RUNBOOK.md`](./AFRIRIDE_PHASE1_SETUP_RUNBOOK.md)

### Current Problem

The authoritative backend stores operational state in memory in:

- [`afriride_system/backend/command_api/command_dispatcher_adapter.py`](../../afriride_system/backend/command_api/command_dispatcher_adapter.py)

Current structures:

- `drivers: dict[str, DriverSession]`
- `rides: dict[str, RideSession]`

This is not pilot-grade durability.

### Proposed Pilot Implementation

Use SQLite first.

Rationale:

- minimal operational complexity
- easy local and pilot deployment
- preserves an upgrade path to PostgreSQL

### Data To Persist

- driver status
- ride state
- ride lifecycle events
- idempotency records
- receipt metadata
- evidence metadata

### Files To Modify

- [`afriride_system/backend/command_api/command_dispatcher_adapter.py`](../../afriride_system/backend/command_api/command_dispatcher_adapter.py)
- [`afriride_system/backend/state.py`](../../afriride_system/backend/state.py)
- [`afriride_system/backend/api_gateway/gateway.py`](../../afriride_system/backend/api_gateway/gateway.py)
- [`afriride_system/api/dispatcher_adapter.py`](../../afriride_system/api/dispatcher_adapter.py)
- [`afriride_system/api/idempotency.py`](../../afriride_system/api/idempotency.py)

### New Files Likely Required

- `afriride_system/backend/storage.py`
- `afriride_system/backend/repositories/driver_repository.py`
- `afriride_system/backend/repositories/ride_repository.py`
- `afriride_system/backend/repositories/idempotency_repository.py`

Exact naming may vary, but the separation should be explicit.

### Acceptance Criteria

- restarting the API process does not erase rides
- restarting the API process does not erase driver online state unless intentionally designed
- ride status queries return previously stored rides after restart
- idempotency behavior survives restart for the configured window

### Tests Required

- persistence round-trip tests
- restart simulation tests
- idempotency durability tests
- lifecycle flow tests against persistent storage

### Pilot Gate

`Persistence = PASS`

## Phase 2: Authentication

### Goal

Enforce separate rider, driver, and operator authority boundaries in the authoritative FastAPI spine.

### Current Problem

The chosen production backend does not yet present a coherent production authentication boundary across:

- rider
- driver
- operator

### Proposed Pilot Implementation

Use JWT authentication with explicit role claims.

Minimum roles:

- `RIDER`
- `DRIVER`
- `OPERATOR`

### Scope

Protect mutating endpoints first:

- passenger ride request and cancel
- driver status, accept, start, complete
- ride contract endpoints
- any operator conversation or trust endpoint added to the spine

### Files To Modify

- [`afriride_system/api/main.py`](../../afriride_system/api/main.py)
- [`afriride_system/api/passenger_routes.py`](../../afriride_system/api/passenger_routes.py)
- [`afriride_system/api/driver_routes.py`](../../afriride_system/api/driver_routes.py)
- [`afriride_system/api/ride_routes.py`](../../afriride_system/api/ride_routes.py)
- [`afriride_system/api/schemas.py`](../../afriride_system/api/schemas.py)

### New Files Likely Required

- `afriride_system/api/auth.py`
- `afriride_system/api/auth_models.py`
- `afriride_system/tests/test_authentication.py`

### Acceptance Criteria

- rider endpoints reject unauthenticated calls
- driver endpoints reject unauthenticated calls
- operator-only surfaces reject non-operator tokens
- role mismatch produces deterministic 401 or 403 behavior

### Tests Required

- token issuance tests
- role authorization tests
- protected-route tests
- negative tests for missing and invalid tokens

### Pilot Gate

`Authentication = PASS`

## Phase 3: Evidence Durability

### Goal

Replay records, trace lineage, and receipt lineage survive restart.

### Current Problem

The trace evidence path is memory-based in:

- [`afriride_system/backend/trace_enforcement.py`](../../afriride_system/backend/trace_enforcement.py)

Specifically:

- `TRACE_LOG = TraceEventLog()`

This weakens pilot evidence and replay authority after restart.

### Proposed Pilot Implementation

Persist:

- trace events
- ride-linked evidence events
- replay metadata
- receipt metadata

The API may still expose the same evidence summary endpoints, but they must read from durable records.

### Files To Modify

- [`afriride_system/backend/trace_enforcement.py`](../../afriride_system/backend/trace_enforcement.py)
- [`afriride_system/backend/event_ledger.py`](../../afriride_system/backend/event_ledger.py)
- [`afriride_system/backend/ledger_receipts.py`](../../afriride_system/backend/ledger_receipts.py)
- [`afriride_system/api/trace_middleware.py`](../../afriride_system/api/trace_middleware.py)
- [`afriride_system/api/main.py`](../../afriride_system/api/main.py)

### New Files Likely Required

- `afriride_system/backend/repositories/trace_repository.py`
- `afriride_system/backend/repositories/evidence_repository.py`
- `afriride_system/backend/repositories/receipt_repository.py`

### Acceptance Criteria

- trace summaries remain available after restart
- ride trace validation remains available after restart
- receipts remain derivable from stored evidence after restart
- evidence endpoints no longer depend on process-local memory for authority

### Tests Required

- trace persistence tests
- evidence summary tests using persisted fixtures
- receipt regeneration tests from persisted records
- restart durability tests

### Pilot Gate

`Evidence = PASS`

`Replay = PASS`

`Receipt = PASS`

## Phase 4: Dashboard Contract Alignment

### Goal

The authoritative dashboard must depend only on endpoints provided by the authoritative backend spine.

### Current Problem

The dashboard currently expects:

- `/rides/active`
- `/system/replay/health`
- `/system/evidence`
- `/system/guards`
- `/trust/conversation`

The first four exist in the chosen FastAPI spine.
`/trust/conversation` currently does not.

### Decision Rule

Choose the smallest valid change.

### Option A

Implement `/trust/conversation` in the chosen FastAPI spine.

### Option B

Remove the dependency from the dashboard.

For a controlled pilot, prefer whichever option:

- reduces scope
- avoids pulling authority from non-spine code
- does not create a second backend dependency

### Files To Modify

If implementing:

- [`afriride_system/api/main.py`](../../afriride_system/api/main.py)
- new route or router file under `afriride_system/api/`

If removing:

- [`dashboard/src/App.jsx`](../../dashboard/src/App.jsx)
- [`dashboard/tests/test_operator_dashboard_surface.py`](../../dashboard/tests/test_operator_dashboard_surface.py)

### Acceptance Criteria

- the dashboard uses only endpoints served by `afriride_system`
- no operator workflow depends on Django or alternate backend surfaces
- dashboard tests match the authoritative backend contract

### Tests Required

- dashboard contract tests
- end-to-end operator flow smoke test
- backend route test if `/trust/conversation` is added

### Pilot Gate

`Dashboard = PASS`

## Cross-Cutting Rules

### Rule 1

Do not add new product features outside:

- `afriride_system`
- `AfriRideMobile`
- `dashboard`

### Rule 2

Do not satisfy pilot blockers by wiring the dashboard or mobile app back into archived or experimental backends.

### Rule 3

If `afritech` is used, document the exact module dependency and classify it as production-supporting platform code.

### Rule 4

Any new persistence or auth code must land inside the authoritative spine, not in `ecosystems/afriride`, `afriride_backend`, or `afriride_system/django_app`.

## Files Likely To Gain New Test Coverage

- [`afriride_system/tests/test_api_flow.py`](../../afriride_system/tests/test_api_flow.py)
- [`afriride_system/tests/test_api_idempotency_hardening.py`](../../afriride_system/tests/test_api_idempotency_hardening.py)
- [`afriride_system/tests/test_trace_enforcement.py`](../../afriride_system/tests/test_trace_enforcement.py)
- [`afriride_system/tests/test_ledger_receipts.py`](../../afriride_system/tests/test_ledger_receipts.py)
- [`dashboard/tests/test_operator_dashboard_surface.py`](../../dashboard/tests/test_operator_dashboard_surface.py)

Additional new tests should be added for:

- persistence restart durability
- authentication role boundaries
- evidence persistence
- dashboard/backend contract alignment

## Suggested Delivery Order

1. persistence
2. evidence durability
3. authentication
4. dashboard contract alignment

Persistence is first by necessity.
Evidence durability follows immediately because it depends on persistence.
Authentication can proceed in parallel in implementation terms, but not as the first gate if evidence and state remain volatile.

## Completion Definition

This execution plan is complete when all of the following are true:

- `Persistence = PASS`
- `Authentication = PASS`
- `Evidence = PASS`
- `Replay = PASS`
- `Receipt = PASS`
- `Dashboard = PASS`

and the controlled pilot no longer depends on process-local in-memory authority for core operational truth.

## Final Gate Position

Current state:

```text
Architecture Authority: established
Operational Durability: incomplete
Pilot Certification: not yet ready
```

Target state after this plan:

```text
Architecture Authority: established
Operational Durability: adequate for controlled pilot
Pilot Certification: eligible for controlled pilot gate review
```
