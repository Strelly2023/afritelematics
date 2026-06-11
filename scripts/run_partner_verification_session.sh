#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 4 ]; then
  echo "usage: ./scripts/run_partner_verification_session.sh --base-url <url> --partner <name> [--expect-network sepolia|mainnet] [--report-out path] [--format text|json]" >&2
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${ROOT_DIR}/venv/bin/python"

if [ -x "$PYTHON_BIN" ]; then
  "$PYTHON_BIN" -m afritech.tools.partner_verification_session_cli "$@"
else
  python3 -m afritech.tools.partner_verification_session_cli "$@"
fi
