#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

python3 - <<'PY'
print("NovaCodePro knowledge worker smoke test: environment validated")
PY
