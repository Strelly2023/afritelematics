#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE="$ROOT/deploy/novaride/compose.operational.yml"
docker compose -f "$COMPOSE" ps --format json
curl --fail --silent --show-error http://127.0.0.1:8101/health >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8102/health >/dev/null
docker compose -f "$COMPOSE" exec -T postgres pg_isready -U novaride -d novaride
docker compose -f "$COMPOSE" exec -T redis redis-cli ping
docker compose -f "$COMPOSE" exec -T kafka /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null
