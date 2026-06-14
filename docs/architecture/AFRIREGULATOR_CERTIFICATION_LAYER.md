# AfriRide Regulator Certification Layer

ADR-0035 introduces a read-only certification surface for external certification consumers.

## Purpose

Certify mobility operations using proof-backed evidence without turning the regulator into truth, replay, settlement, or dispatch authority.

## Boundary

- Regulator is a certification consumer only.
- Regulator cannot override proof, replay, settlement, dispatch, custody, or trust.
- Certification artifacts must remain deterministic and hash-stable.

## Core artifacts

- `afritech.mobility.regulator_certification_layer`
- `afritech.tests.mobility.test_regulator_certification_layer`
- `afritech/governance/adr/ADR-0035-regulator-certification-layer.yaml`

