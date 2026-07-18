#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 -m pytest afritech/tests/novacodepro/test_ncp006b_design_service.py -q
