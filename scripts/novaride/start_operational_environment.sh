#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE="$ROOT/deploy/novaride/compose.operational.yml"
: "${POSTGRES_PASSWORD:?set POSTGRES_PASSWORD without printing it}"
docker info >/dev/null
docker compose -f "$COMPOSE" config --quiet
docker compose -f "$COMPOSE" up -d --build --wait
"$ROOT/scripts/novaride/check_operational_environment.sh"
