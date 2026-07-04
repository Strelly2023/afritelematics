#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

python3 -m pytest -q --maxfail=0
python3 -m afritech.ci.four_gate_validator
python3 -m afritech.guards.guard_runtime_boundary_governance --fail-on-drift
python3 -m afritech.ci.secret_scan
python3 -m afritech.ci.docs_link_validator
npm --prefix dashboard run build
npm --prefix rider_app run typecheck
npm --prefix driver_app run typecheck
git diff --check
