#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python3 scripts/api/generate_api_contracts.py
python3 scripts/api/verify_api_contracts.py
python3 scripts/api/generate_sdk_artifacts.py
python3 scripts/api/verify_generated_sdks.py
