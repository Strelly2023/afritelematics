#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
./venv/bin/python3 -m afritech.novacodepro.operations_worker "$@"
