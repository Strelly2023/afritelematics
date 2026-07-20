# NovaRide current state

Audit date: 2026-07-18 UTC
Source commit: `63ef5e0c94333d5482ede1c19b13db908ad76e7d`

NovaRide is a mature multi-surface mobility platform, not a greenfield repository. Its canonical backend lives in `afritech/novaride_runtime` and `afritech/api/novaride_runtime_api.py`. Rider and driver Expo applications, operations/dispatch/support/fleet portals, shared TypeScript packages, PostgreSQL migrations, Redis/Kafka coordination, observability assets, deployment manifests, and signed Android pilot artifacts already exist.

The implementation includes rider and driver lifecycle flows, dispatch and pricing, trip state machines, safety incidents, payments/wallet adapters, corporate/fleet/logistics/transit modules, durable outbox processing, replay controls, read models, regional configuration, resilience, and controlled-pilot evidence.

This execution added the supplied NovaRide brand asset to both mobile applications and generated a consolidated, commit-bound release evidence set. Existing unrelated NovaID working-tree changes were preserved.

Current verified level: **CONTROLLED_PILOT_CANDIDATE**, subject to the blockers in the final evidence directory. Production or general availability is not asserted.
