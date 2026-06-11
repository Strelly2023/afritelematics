# AFRIRIDE_PILOT_READINESS

## Status

Working readiness scorecard for the authoritative AfriRide production spine defined in:

[`AFRIRIDE_PRODUCTION_SPINE.md`](../architecture/AFRIRIDE_PRODUCTION_SPINE.md)

This scorecard evaluates only the chosen spine:

- [`afriride_system`](../../afriride_system)
- [`AfriRideMobile`](../../AfriRideMobile)
- [`dashboard`](../../dashboard)
- selected replay/proof/runtime support from [`afritech`](../../afritech)

It does not grant production authority to any archived or experimental implementation line.

## Scoring Model

- `PASS`: implemented and evidenced in the production spine
- `PARTIAL`: implemented in some form, but incomplete, weakly integrated, or not yet operationally sufficient
- `FAIL`: missing or materially unsuitable for controlled pilot execution

## Scorecard

| Surface | Status | Assessment |
| --- | --- | --- |
| Backend API | PASS | Deployed path is explicit in [`render.yaml`](../../render.yaml) and the FastAPI entrypoint exists in [`afriride_system/api/main.py`](../../afriride_system/api/main.py). Core request/accept/start/complete flows are covered in [`afriride_system/tests/test_api_flow.py`](../../afriride_system/tests/test_api_flow.py). |
| Mobile | PARTIAL | [`AfriRideMobile`](../../AfriRideMobile) is the consolidated client path and documents rider/driver/operator workflows, but it remains a scaffold-level surface and field readiness is not yet proven. |
| Dashboard | PARTIAL | [`dashboard`](../../dashboard) is the authoritative operator web surface and is tested against replay/evidence endpoints, but it depends on `/trust/conversation`, which is not present in the deployed `afriride_system` FastAPI spine. |
| Persistence | FAIL | Current backend state is process-local and in-memory. [`AfriRideCommandDispatcher`](../../afriride_system/backend/command_api/command_dispatcher_adapter.py) stores `drivers` and `rides` in dictionaries, which is not sufficient for pilot-grade durability. |
| Replay | PARTIAL | Replay and trace validation are present through [`afriride_system/backend/event_ledger.py`](../../afriride_system/backend/event_ledger.py), [`afriride_system/backend/trace_enforcement.py`](../../afriride_system/backend/trace_enforcement.py), and supporting tests, but the operational path is still lightweight and not backed by durable storage. |
| Receipt | PARTIAL | Receipt and ledger proof generation exist in [`afriride_system/backend/ledger_receipts.py`](../../afriride_system/backend/ledger_receipts.py) and related ride routes, but they are derived from in-memory ride/event state rather than durable production records. |
| Driver Lifecycle | PASS | Online, assignment, start, complete, and contract routes exist in the production spine and are covered by API flow tests. |
| Rider Lifecycle | PASS | Ride request, status, and cancel routes are implemented in [`afriride_system/api/passenger_routes.py`](../../afriride_system/api/passenger_routes.py) and exercised in test coverage. |
| Evidence | PARTIAL | Evidence and integrity summaries are exposed from the production API, but the current evidence log is in-memory via [`TRACE_LOG`](../../afriride_system/backend/trace_enforcement.py), which weakens audit durability. |
| Deployment | PASS | Deployment target is explicit and singular: `uvicorn afriride_system.api.main:app` in [`render.yaml`](../../render.yaml). |

## Secondary Readiness Surfaces

| Surface | Status | Assessment |
| --- | --- | --- |
| Authentication | FAIL | The chosen FastAPI spine does not currently enforce a coherent production authentication boundary across rider, driver, and operator flows. |
| Payments | PARTIAL | Earnings and receipt-style outputs exist, but no clearly authoritative, production-grade payment integration is present in the chosen spine. |
| Observability | PARTIAL | Replay health, evidence, and guard endpoints exist, but broader operational observability is still narrow and pilot-specific. |
| Platform Support | PARTIAL | `afritech` contains useful replay/proof/runtime support, but the exact module subset retained in the spine is not yet formally extracted. |

## Evidence Notes

### Backend API

The production backend is the deployed FastAPI surface:

- [`afriride_system/api/main.py`](../../afriride_system/api/main.py)
- [`render.yaml`](../../render.yaml)

Core rider and driver flows are exercised in:

- [`afriride_system/tests/test_api_flow.py`](../../afriride_system/tests/test_api_flow.py)

### Persistence

Current state handling is not pilot-grade persistent storage.

[`AfriRideCommandDispatcher`](../../afriride_system/backend/command_api/command_dispatcher_adapter.py) stores backend truth in in-memory dictionaries:

- `drivers: dict[str, DriverSession]`
- `rides: dict[str, RideSession]`

That means state is lost on process restart and cannot serve as strong operational evidence by itself.

### Replay And Evidence

Replay/evidence capability clearly exists:

- [`afriride_system/backend/event_ledger.py`](../../afriride_system/backend/event_ledger.py)
- [`afriride_system/backend/ledger_receipts.py`](../../afriride_system/backend/ledger_receipts.py)
- [`afriride_system/backend/trace_enforcement.py`](../../afriride_system/backend/trace_enforcement.py)
- [`afriride_system/tests/test_event_ledger_validation.py`](../../afriride_system/tests/test_event_ledger_validation.py)

But the active evidence path remains lightweight because trace state is kept in memory.

### Dashboard Gap

The operator dashboard polls valid production endpoints for:

- `/rides/active`
- `/system/replay/health`
- `/system/evidence`
- `/system/guards`

However it also calls:

- `/trust/conversation`

That route appears in non-spine surfaces, not in the deployed `afriride_system` FastAPI service. This is a current integration gap for the chosen spine.

## Tier Assessment

### Tier 1: Must Have

| Item | Status |
| --- | --- |
| deployed backend | PASS |
| persistent storage strategy | FAIL |
| rider and driver mobile workflows | PARTIAL |
| receipt generation | PARTIAL |
| replay generation and verification | PARTIAL |
| operational dashboard | PARTIAL |
| evidence capture and trace integrity | PARTIAL |

### Tier 2: Should Have

| Item | Status |
| --- | --- |
| payment integration | PARTIAL |
| driver earnings | PARTIAL |
| trip analytics | PARTIAL |
| trust metrics | PARTIAL |
| bounded fraud detection | FAIL |

### Tier 3: Later

Not scored for current controlled pilot gate.

## Current Pilot Blockers

The primary blockers to a stronger pilot-readiness claim are:

1. no durable persistence in the production backend
2. in-memory evidence and trace authority
3. incomplete authentication boundary on the chosen FastAPI spine
4. dashboard dependency on at least one route outside the chosen production backend
5. receipt and replay outputs not yet grounded in durable operational records

## Required Next Actions

1. Add durable persistence for rides, driver state, and evidence records within `afriride_system`.
2. Move trace and replay evidence from in-memory runtime state to persistent storage.
3. Define and enforce the authentication model for rider, driver, and operator surfaces.
4. Either implement `/trust/conversation` inside the chosen spine or remove that dependency from `dashboard`.
5. Produce an explicit list of `afritech` modules that remain in the production spine as support modules.

## Gate Position

Current gate position:

`not yet ready for strong controlled pilot claim`

Reason:

The production spine now has architectural authority, but operational readiness still has clear FAIL and PARTIAL surfaces in persistence, evidence durability, authentication, and dashboard integration.
