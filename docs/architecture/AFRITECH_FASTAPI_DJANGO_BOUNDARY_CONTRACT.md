# AfriTech FastAPI vs Django Boundary Contract

Status: AFRITECH FASTAPI VS DJANGO BOUNDARY CONTRACT

Classification: BOUNDED RUNTIME SEPARATION CONTRACT

Purpose: define the strict contract between the FastAPI runtime surface and the
Django-configured state surface so startup, deployment, and replay behavior stay
predictable.

This contract constrains runtime coordination. It is not proof that every
existing module already obeys it.

## Boundary Statement

FastAPI owns:

- request admission
- token issuance and verification
- edge normalization
- queue / worker orchestration
- public verification routing
- dashboard-facing observation routes

Django owns:

- ORM-backed models
- configured app registry
- `INSTALLED_APPS`
- Django settings
- admin / DRF-era view surfaces
- stateful persistence conventions tied to Django models

## Hard Rule

FastAPI import time must not require Django settings.

If a module touches:

- `django.db`
- `django.conf.settings`
- `django.apps`
- `rest_framework`
- model classes inheriting `models.Model`

then that module is Django-bound and must not execute during FastAPI import
time unless Django is explicitly initialized first.

## Allowed FastAPI -> Django Paths

Allowed:

- lazy import inside a function
- lazy model lookup behind a helper like `_get_api_key_model()`
- explicit `DJANGO_SETTINGS_MODULE` setup before `django.setup()`
- service adapters that initialize Django only at runtime boundary points

Allowed example:

```text
FastAPI route
-> helper function
-> ensure DJANGO_SETTINGS_MODULE exists
-> django.setup() if apps not ready
-> import Django model
-> execute stateful operation
```

## Forbidden FastAPI -> Django Paths

Forbidden:

- top-level import of Django model classes in FastAPI startup modules
- top-level import of DRF `Response`, `APIView`, or decorators in startup path
- importing modules that access `settings.INSTALLED_APPS` at import time
- calling model managers during module import
- importing legacy Django-only auth modules directly into startup graph without guards

## Startup-Safe Module Criteria

A FastAPI-startup-safe module:

- imports only pure Python or runtime-safe dependencies
- does not require Django settings
- does not require DRF to exist
- does not import ORM models at module import time
- can be loaded inside `uvicorn afritech.api.app:app` without side effects

## Django-Bound Module Criteria

A Django-bound module:

- imports `django.*`
- imports `rest_framework.*`
- defines `models.Model`
- expects app registry readiness
- expects configured email, admin, or ORM surfaces

These modules must sit behind explicit runtime coordination.

## Required Initialization Sequence

```text
1. FastAPI process starts
2. FastAPI imports startup-safe modules
3. Request hits Django-bound path
4. Runtime helper sets DJANGO_SETTINGS_MODULE if absent
5. Runtime helper calls django.setup() if apps not ready
6. Django-bound model/service is imported
7. Stateful operation executes
```

## Contract For Legacy Modules

Legacy modules may remain in the repo if all of the following are true:

- import-safe fallback exists when DRF is absent
- Django model import is lazy
- startup path does not force app-registry access
- production runtime can bypass legacy surfaces safely

## Runtime Ownership Matrix

| Concern | Owner |
| --- | --- |
| HTTP admission | FastAPI |
| JWT device auth | FastAPI |
| WebSocket auth | FastAPI |
| Input normalization | FastAPI / edge |
| Queue routing | FastAPI / execution |
| ORM models | Django |
| Admin / DRF surfaces | Django |
| Proof and receipt serialization | shared pure-Python surface |
| Public verification endpoint | FastAPI |
| Dashboard preview | separate UI container |

## Enforcement Intention

This contract should be checked by:

- import-topology validators
- deployment smoke tests
- startup health probes
- runtime map review during production changes

## Non-Claims

This contract does not say:

- Django must be removed from the platform
- FastAPI must never call Django
- all legacy views are production-active
- every current module already obeys the boundary

It says:

- FastAPI and Django may coexist
- they must coexist through explicit runtime coordination
- import-time coupling is the primary thing to prevent
