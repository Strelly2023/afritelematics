# AFRIRIDE_PRODUCTION_SPINE

## Status

Authoritative for the controlled AfriRide pilot until explicitly replaced by a later architecture decision record.

## Purpose

This document removes ambiguity about which implementation path is real.

AfriRide currently contains multiple backend and client implementation lines.
That condition is incompatible with controlled pilot execution.

The production spine defined here establishes:

- one authoritative backend
- one authoritative mobile client path
- one authoritative operator dashboard
- one authoritative replay and proof support path
- one authoritative deployment path

Everything else must either:

- support this spine
- be archived
- or be explicitly marked experimental

## Authoritative Production Spine

### Backend

Authoritative backend:

`afriride_system`

Authoritative backend entrypoint:

[`afriride_system/api/main.py`](../../afriride_system/api/main.py)

Authoritative deployment path:

`uvicorn afriride_system.api.main:app`

Source of deployment truth:

[`render.yaml`](../../render.yaml)

### Mobile

Authoritative mobile application:

`AfriRideMobile`

Source path:

[`AfriRideMobile`](../../AfriRideMobile)

This is the only production mobile surface for the controlled pilot.

### Dashboard

Authoritative operator dashboard:

`dashboard`

Source path:

[`dashboard`](../../dashboard)

This is the only production web dashboard surface for the controlled pilot.

### Replay / Proof / Runtime Support

Authoritative platform support path:

selected modules from `afritech`

These modules are kept only where they directly support:

- replay verification
- proof generation or validation
- runtime verification
- trace inspection
- pilot evidence discipline

`afritech` is not the production backend for AfriRide.
It is the platform support layer behind the production spine.

## Non-Authoritative Implementation Lines

The following paths are not production authorities for the controlled AfriRide pilot:

- `afriride_backend`
- `ecosystems/afriride`
- `afriride_system/django_app`
- `afriride-driver`
- `driver_app`
- `rider_app`
- `replay_dashboard`

Their classification must be one of:

- archived reference
- experimental research
- migration source for the production spine

They must not define:

- canonical backend truth
- canonical API contracts
- deployment defaults
- pilot readiness claims

## Architectural Rule

AfriRide pilot execution must follow:

```text
one authority
one execution path
one operational truth
```

It must not operate under:

```text
multiple competing backends
multiple competing clients
multiple competing deployment surfaces
```

## Support Boundary

Code is part of the production spine only if it does at least one of the following:

1. Runs the deployed backend.
2. Runs the production mobile app.
3. Runs the production operator dashboard.
4. Provides replay, proof, runtime, trace, or evidence capability used by that path.
5. Tests or deploys the above.

If a module does not satisfy one of those conditions, it is not part of the production spine.

## Repository Classification Policy

### Keep

Keep paths that directly power the production spine:

- `afriride_system`
- `AfriRideMobile`
- `dashboard`
- supporting `afritech` replay/proof/runtime modules
- active shared schemas, scripts, tests, traces, and docs

### Archive

Archive paths that duplicate the spine or represent obsolete scaffolds.

Archive does not mean delete.
Archive means:

- retained for reference
- not authoritative
- not part of active deployment
- not part of default CI scope unless explicitly needed

### Experimental

Experimental paths may continue as research lines, but they must be labeled clearly and must not compete with the production spine.

### Merge

Reusable code from non-authoritative paths may be merged into the production spine only if:

1. ownership is explicit
2. tests move with it
3. API and operational boundaries remain unchanged unless intentionally versioned

## Pilot Readiness Scope

Repository cleanup alone does not create operational readiness.

The production spine must be evaluated against the following pilot readiness surfaces:

| Area | Required For Pilot |
| --- | --- |
| Backend API | Yes |
| Mobile App | Yes |
| Dashboard | Yes |
| Persistence | Yes |
| Replay Engine | Yes |
| Receipts | Yes |
| Authentication | Yes |
| Driver Workflow | Yes |
| Rider Workflow | Yes |
| Evidence Generation | Yes |
| Payments | Conditional / staged |
| Driver Earnings | Conditional / staged |
| Analytics | Later |
| Fraud Detection | Later |
| Trust Metrics | Later |

## Priority Tiers

### Tier 1: Must Have

- deployed backend on `afriride_system`
- persistent storage strategy
- rider and driver mobile workflows through `AfriRideMobile`
- receipt generation
- replay generation and verification
- operational dashboard
- evidence capture and trace integrity

### Tier 2: Should Have

- payment integration
- driver earnings
- trip analytics
- trust metrics
- bounded fraud detection

### Tier 3: Later

- regional deployment expansion
- subscriptions
- public transport integration
- marketplace or ecosystem extensions

## Immediate Consequences

The following decisions apply now:

1. `render.yaml` remains bound to `afriride_system.api.main:app`.
2. New backend product work must land in `afriride_system` unless a formal architecture decision replaces it.
3. New mobile product work must land in `AfriRideMobile`.
4. New operator web work must land in `dashboard`.
5. `afritech` changes must identify whether they are runtime support for AfriRide or separate platform work.
6. Duplicate backends and duplicate clients must not receive production-signaling documentation or deployment defaults.

## Decision Record

Until superseded, the controlled AfriRide pilot recognizes:

- authoritative backend: `afriride_system`
- authoritative mobile app: `AfriRideMobile`
- authoritative dashboard: `dashboard`
- authoritative replay/proof/runtime support: selected `afritech` modules
- authoritative deployment path: `render.yaml` -> `afriride_system.api.main:app`

## Next Deliverables

The next architecture deliverables should be:

1. a consolidation matrix for every top-level directory
2. a list of `afritech` modules that remain in the spine
3. a pilot-readiness scorecard with pass/fail status
4. a phased migration and archive plan
