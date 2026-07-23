#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
COMMIT="$(git rev-parse HEAD)"
echo "NovaRide traceability validation commit=$COMMIT"
echo "+ python3 -m afritech.ci.novaride_requirements_validator --json"
python3 -m afritech.ci.novaride_requirements_validator --json
