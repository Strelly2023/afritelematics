#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -s .pytest_cache/v/cache/lastfailed ]]; then
  exec python3 -m pytest --last-failed
fi

echo "No last-failed cache found; running fast developer tests instead."
exec "$ROOT_DIR/scripts/test_fast.sh"
