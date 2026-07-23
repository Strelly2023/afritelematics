#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
echo "+ python3 -m afritech.ci.novaride_requirements_validator"
python3 -m afritech.ci.novaride_requirements_validator
