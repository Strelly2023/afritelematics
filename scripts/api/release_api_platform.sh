#!/usr/bin/env bash
set -euo pipefail

python3 -m compileall -q afritech/api_catalog afritech/api
python3 -m pytest -q tests/api_catalog
python3 -m afritech.guards.guard_api_catalog
python3 -m afritech.guards.guard_openapi_governance
python3 -m afritech.guards.guard_api_compatibility
python3 -m afritech.guards.guard_api_breaking_changes
python3 scripts/api/generate_api_contracts.py
python3 scripts/api/verify_api_contracts.py
bash scripts/api/generate_sdks.sh
python3 scripts/api/verify_generated_sdks.py
python3 scripts/api/verify_release_provenance.py
python3 scripts/api/verify_contract_approvals.py

echo "nova_api_platform_release_gate=PASS"
