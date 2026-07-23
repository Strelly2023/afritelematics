# NovaRide current state

Audit date: 2026-07-23 Australia/Melbourne

Baseline commit: `94ba38da884ca9676cb500a7d32cac14ecefa055`

Branch: `feature/product-factory-enterprise-sdlc`

Remote baseline: `origin/feature/product-factory-enterprise-sdlc` at the same commit. The local branch has no configured upstream, so remote comparisons and pushes must name the remote branch explicitly.

## Authoritative implementation

NovaRide is a mature multi-surface mobility platform. Its canonical backend is `afritech/novaride_runtime` exposed by `afritech/api/novaride_runtime_api.py`. Canonical durable runtime state uses PostgreSQL repositories and migrations, Redis coordination, Kafka publishing, a transactional outbox, replay controls, and operational read models. Mobile clients and portals must not become authoritative for pricing, dispatch, trip transitions, payment settlement, or privileged operations.

Primary application surfaces are:

- `rider_app`
- `driver_app`
- `novaride_fleet_app`
- `novaride_operator_app`
- `apps/novaride-operations`
- `apps/novaride-admin`
- `apps/novaride-corporate`
- `apps/novaride-fraud-center`

Other NovaRide-named application directories are not considered implemented merely because a directory or `app.json` exists. A claimed application must build, authenticate, authorise, integrate with a governed backend, have tests, and have a deployment definition.

## Verified strengths

- Rider and driver controlled-pilot journeys.
- Deterministic dispatch and trip state machines.
- Pricing, wallet boundaries, payment-safety controls, and idempotency.
- Safety incidents and operations intervention.
- PostgreSQL migrations and repositories.
- Redis/Kafka coordination, outbox delivery, replay, and read models.
- Tenant-aware security boundaries and regional configuration.
- Versioned Android artifacts, release guards, checksums, and historical evidence.
- SLO, readiness, resilience, deployment, and operations assets.

## Current limitations

- The canonical requirements catalogue contains only 13 controlled-pilot requirements and is bound to commit `63ef5e0c94333d5482ede1c19b13db908ad76e7d`.
- Much of the existing NovaRide evidence is historical, untracked, or bound to that older commit. It cannot certify this baseline.
- Commercial assumptions, primary market research, full enterprise requirements, partner portals, governed ML lifecycle, and the enterprise analytics platform are incomplete.
- Some UI evidence identifies local/prototype state and production mock-path controls as incomplete.
- Production-equivalent PostgreSQL, Redis, Kafka, object-storage, observability, backup, restore, failover, and disaster-recovery validation is not current for this commit.
- The active Python environment lacks `psycopg`, preventing collection of the runtime API contract suite.
- Live payments, independent security assessment, physical Android/iOS validation, real participant pilots, and authenticated approvals require external actors and evidence.

## Baseline test result

The initial representative suite passed 29 tests covering NovaRide application inventory, state machines, release-readiness domains, and GA enablement. Runtime API contract collection was blocked by `ModuleNotFoundError: psycopg`. This is a dependency/environment blocker, not a passing certification.

## Release truth

Current disposition: **CONTROLLED_PILOT_CANDIDATE**, not public-pilot, production-ready, or GA approved.

Promotion is prohibited until current-commit evidence closes the applicable gates and the required authenticated approvals exist.
