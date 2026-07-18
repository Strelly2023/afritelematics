#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 -m pytest \
  afritech/tests/api/test_novacodepro_ncp007_api.py \
  afritech/tests/novacodepro/test_ncp007_development_service.py \
  -q
