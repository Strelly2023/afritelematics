# NL-001 — Logistics domain foundation

## Objective and baseline reused

Establish immutable, tenant-aware domain contracts and lifecycle aggregates for NovaLogistics. Reused the existing mobility custody-chain, settlement boundary, geographic types, public website, and existing import paths without modification.

## Files added

- `afritech/novalogistics/__init__.py`
- `afritech/novalogistics/domain.py`
- `afritech/tests/novalogistics/__init__.py`
- `afritech/tests/novalogistics/test_domain_foundation.py`
- NovaLogistics baseline and NL-001 evidence under `artifacts/novalogistics/`

No existing production file was modified. No migration or API was introduced in this domain-only section.

## Domain contracts

- Normalized identifiers, addresses, contacts, and geographic coordinates.
- Immutable, tenant-scoped reference entities for every required NL-001 noun.
- Versioned domain events with UTC enforcement and immutable event data.
- Quote, order, shipment/consignment, load, stop, pickup, delivery, return, claim, and incident state machines.
- Illegal-transition enforcement, idempotent same-state replay, optimistic version field, serialization, and deserialization.
- Stable package exports through `afritech.novalogistics`.

## Commands and results

- `./venv/bin/python -m pytest -q afritech/tests/novalogistics/test_domain_foundation.py` — PASS, 11 tests.
- `./venv/bin/python -m compileall -q afritech/novalogistics afritech/tests/novalogistics` — PASS.
- `./venv/bin/python -m pytest -q afritech/tests/novalogistics afritech/tests/mobility/test_logistics_custody_chain.py afritech/tests/mobility/test_settlement_boundary.py afritech/tests/distributed/test_africonnecttl_surface.py` — PASS, 50 tests.
- `node --test tests/novadashdoor-novalogistics.test.js` from `apps/public-web` — PASS, 5 tests.
- `git diff --check -- afritech/novalogistics afritech/tests/novalogistics artifacts/novalogistics` — PASS.

## Known limitations and release impact

Persistence, migrations, APIs, authorization, and external integrations are deliberately deferred to their numbered sections. The domain foundation is production-oriented and its focused and compatibility suites pass. Runtime-boundary recovery isolated nine unrelated untracked Python modules, regenerated the governed scan from the approved repository scope, and passed the governance guard before commit.

External dependencies: none. The original blocker and its resolution are recorded in `artifacts/novalogistics/blockers/NL-001-blocker.md`.
