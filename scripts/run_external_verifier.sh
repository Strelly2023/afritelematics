#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 2 ]; then
  echo "usage: ./scripts/run_external_verifier.sh --proof <path-or-url> [--chain <path-or-url>] [--demo <path-or-url>] [--trust-dashboard <path-or-url>] [--base-url <url>] [--format text|json]" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/venv/bin/python"

if [ -x "$PYTHON_BIN" ]; then
  "$PYTHON_BIN" -m afritech.tools.external_verifier_cli "$@"
else
  python3 -m afritech.tools.external_verifier_cli "$@"
fi
