#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
./venv/bin/python -m pytest \
  afritech/tests/api/test_novacodepro_ncp008_api.py \
  afritech/tests/novacodepro/test_ncp008_operations_service.py \
  -q
cd novacodepro_portal
npm test -- --test-name-pattern "NCP-008"
