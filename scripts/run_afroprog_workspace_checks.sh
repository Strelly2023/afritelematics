#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PY="$ROOT/venv/bin/python"

if [ ! -x "$VENV_PY" ]; then
  echo "Missing virtualenv python at $VENV_PY" >&2
  exit 1
fi

echo "Running AfriPro workspace Python checks with venv..."
"$VENV_PY" -m pytest \
  afritech/tests/apps/test_afroprog_workspace.py \
  afritech/tests/apps/test_afroprog_workspace_governance.py \
  afritech/tests/apps/test_afroprog_django_runtime.py \
  afritech/tests/api/test_afroprog_workspace_api.py \
  afritech/tests/api/test_dashboard_gateway_api.py \
  afritech/tests/architecture/test_afritech_dashboard_services.py \
  afritech/tests/architecture/test_afritech_dashboard_views.py \
  afritech/tests/architecture/test_dashboard_router.py \
  -q

echo "Running React dashboard build..."
cd "$ROOT/dashboard"
if command -v npm >/dev/null 2>&1; then
  npm run build
elif zsh -lic 'command -v npm >/dev/null 2>&1'; then
  zsh -lic "cd '$ROOT/dashboard' && npm run build"
elif [ -x "$ROOT/dashboard/node_modules/.bin/vite" ]; then
  "${NODE_BIN:-/Applications/Codex.app/Contents/Resources/node}" \
    "$ROOT/dashboard/node_modules/vite/bin/vite.js" build
else
  echo "No npm or local vite binary available for dashboard build" >&2
  exit 1
fi
