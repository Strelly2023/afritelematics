#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

if [ ! -f novacodepro_portal/package.json ]; then
  echo "novacodepro_portal package.json not found" >&2
  exit 1
fi

cd novacodepro_portal
if npm run | grep -q "test:e2e"; then
  npm run test:e2e
else
  echo "test:e2e script not configured" >&2
  exit 1
fi
