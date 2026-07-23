# NovaRide 11-phase baseline

This baseline is the controlling implementation map for the NovaRide GA completion programme. It separates code presence, test execution, operational evidence, and approval so that historical artifacts cannot silently certify a newer release.

## Baseline identity

- Branch: `feature/product-factory-enterprise-sdlc`
- Commit: `94ba38da884ca9676cb500a7d32cac14ecefa055`
- Remote reference: `origin/feature/product-factory-enterprise-sdlc`
- Previous principal evidence commit: `63ef5e0c94333d5482ede1c19b13db908ad76e7d`
- Working-tree condition at discovery: tracked files clean; substantial pre-existing untracked evidence and generated outputs present
- Git LFS: client unavailable in the active environment
- Submodules: none reported

## Evidence rules

Evidence is certifying only when it records the release commit, command, tool versions, environment, timestamp, outcome, artifact identity, and—where required—an attributable approval. Evidence bound only to `63ef5e0c...` is historical. Untracked artifacts are preserved but are not automatically part of a release candidate.

## Canonical boundaries

| Concern | Canonical location | Authority rule |
|---|---|---|
| Mobility runtime | `afritech/novaride_runtime` | Server owns domain transitions |
| API | `afritech/api/novaride_runtime_api.py` | Authenticated, tenant/region-scoped commands |
| Persistence | `afritech/novaride_runtime/persistence` | PostgreSQL for production authority |
| Events | `afritech/novaride_runtime/events` | Outbox, schema compatibility and replay controls |
| Rider | `rider_app` | Client state is non-authoritative |
| Driver | `driver_app` | Offline commands require governed synchronisation |
| Fleet | `novaride_fleet_app` and runtime fleet domain | Server owns assignments/compliance |
| Operator | `novaride_operator_app`, `apps/novaride-operations` | Privileged actions require policy and audit |
| Identity | NovaID integration boundary | No local identity bypass in production |
| Payments | wallet/NovaPay adapter boundary | Live mode requires explicit gates |

## Phase entry conditions

Each phase requires requirements, accountable owners, implementation, integration, executable tests, security controls, current evidence, documented limitations, and required approvals. Missing external evidence is recorded as blocked, never synthesized.

## Baseline validation

- 29 representative tests passed.
- Runtime API contract collection was blocked by missing `psycopg`.
- No current release candidate is selected.
- No GA approval is asserted.

The baseline disposition is **CONTROLLED_PILOT_CANDIDATE**.
