#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="${BASE:-origin/main}"
HEAD="${HEAD:-HEAD}"

cd "$ROOT_DIR"

python3 -m afritech.ci.impact --base "$BASE" --head "$HEAD"

if grep -q '"full_validation_required": true' ci_artifacts/impact_plan.json; then
  echo "Impact analysis requires full validation; escalating to release validation."
  exec "$ROOT_DIR/scripts/test_release.sh"
fi

exec python3 -m afritech.ci.run_selected_tests --plan ci_artifacts/impact_plan.json
