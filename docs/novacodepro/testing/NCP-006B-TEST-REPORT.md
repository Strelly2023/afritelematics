# NCP-006B Test Report

Date: 2026-07-18

## Executed

- `python3 -m pytest afritech/tests/api -k "novacodepro" -q`
- `python3 -m pytest afritech/tests/novacodepro -q`
- `cd novacodepro_portal && npm test`
- `cd novacodepro_portal && npm run build`
- `cd novacodepro_portal && npm run test:e2e`
- `cd novacodepro_portal && npm run test:accessibility`
- `./scripts/novacodepro/design_worker.sh`
- `./scripts/novacodepro/validate_design.sh`
- `./venv/bin/python -m afritech.ci.import_topology_validator`
- `./venv/bin/python -m afritech.ci.constitutional_pipeline`

## Result

Internal backend and portal checks passed. Real browser E2E and dedicated accessibility certification are blocked in this environment and are reported honestly in the portal scripts.
