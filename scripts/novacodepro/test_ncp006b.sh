#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 -m pytest \
  afritech/tests/api/test_novacodepro_design_workspaces_api.py \
  afritech/tests/api/test_novacodepro_design_briefs_api.py \
  afritech/tests/api/test_novacodepro_design_tokens_api.py \
  afritech/tests/api/test_novacodepro_design_components_api.py \
  afritech/tests/api/test_novacodepro_design_traceability_api.py \
  afritech/tests/api/test_novacodepro_design_handoff_api.py \
  -q
