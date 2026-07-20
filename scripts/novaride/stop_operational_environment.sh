#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
docker compose -f "$ROOT/deploy/novaride/compose.operational.yml" down
