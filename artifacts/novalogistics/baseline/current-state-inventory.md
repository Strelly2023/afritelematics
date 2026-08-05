# NovaLogistics current-state inventory

Captured: 2026-08-06 UTC

Branch: `feature/product-factory-enterprise-sdlc`

HEAD: `371c9f7d76ce1ccc4fe6036db6ac63d5b4be6718`

## Canonical and reusable implementation

- `afritech/mobility/logistics_custody_chain.py`: immutable custody steps/chains, validation, deterministic hashes, proof export.
- `afritech/mobility/logistics_custody_invariants.py`: custody invariant evaluation.
- `afritech/mobility/settlement_boundary.py`: shared settlement boundary suitable for future NovaPay integration.
- `afritech/novaride_runtime/logistics/__init__.py`: existing package boundary, currently minimal.
- `ecosystems/afriride/geo/types.py`: reusable geographic point contract.
- `afritech/services/africonnecttl/`: logistics-adjacent execution and API contracts.
- `apps/public-web/src/novalogistics.jsx`: existing public product surface.
- `apps/public-web/tests/novadashdoor-novalogistics.test.js`: existing route/catalog/content coverage.
- `packages/novaride-logistics-ui/`: shared logistics UI package.

## Relevant trees

- Domain/services: `afritech/mobility`, `afritech/services/africonnecttl`, `afritech/novaride_runtime/logistics`
- Tests: `afritech/tests/mobility`, `afritech/tests/distributed`, `apps/public-web/tests`
- Applications/portals: `apps/public-web`, `novaride_fleet_app`, `novaride_fleet_portal`, `novaride_dispatch_portal`, `novaride_operations_portal`
- Shared packages: `packages/novaride-logistics-ui`, `packages/novaride-fleet-ui`, `packages/novaride-dispatch-sdk`, `packages/novaride-api-sdk`
- Deployment: `deploy`, repository container and operational assets (no NovaLogistics-specific deployment found)
- Migrations: no NovaLogistics-specific migration tree found

## Architecture decision for NL-001

Create the canonical product package at `afritech.novalogistics`, reuse the existing custody-chain and geo contracts through compatibility exports/adapters, and avoid changing NovaRide contracts. Business rules belong in immutable domain models rather than HTTP or UI handlers.
