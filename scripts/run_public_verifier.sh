#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "usage: ./scripts/run_public_verifier.sh <packet.json> [--format json|text] [--write-report path]" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/venv/bin/python"

if [ -x "$PYTHON_BIN" ]; then
  "$PYTHON_BIN" -m afritech.verify "$@"
else
  python3 -m afritech.verify "$@"
fi
