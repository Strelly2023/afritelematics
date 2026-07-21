#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="deploy/production/docker-compose.production.yml"
ENV_FILE="deploy/production/.env.production"
BASE_URL=""

usage() {
  cat <<'EOF'
usage: ./scripts/deploy_production_zero_downtime.sh [--compose-file PATH] [--env-file PATH] [--base-url URL]

Performs a rolling production update without taking the full stack down first.
The script updates the API and dashboard services one at a time, waits for
health, then validates the edge configuration and runs the production probe.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --compose-file)
      COMPOSE_FILE="${2:-}"
      if [[ -z "$COMPOSE_FILE" ]]; then
        echo "--compose-file requires a value" >&2
        exit 1
      fi
      shift 2
      ;;
    --env-file)
      ENV_FILE="${2:-}"
      if [[ -z "$ENV_FILE" ]]; then
        echo "--env-file requires a value" >&2
        exit 1
      fi
      shift 2
      ;;
    --base-url)
      BASE_URL="${2:-}"
      if [[ -z "$BASE_URL" ]]; then
        echo "--base-url requires a value" >&2
        exit 1
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "missing compose file: $COMPOSE_FILE" >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "missing env file: $ENV_FILE" >&2
  exit 1
fi

if grep -Eq 'replace-with|your-domain\.example' "$ENV_FILE"; then
  echo "$ENV_FILE still contains placeholder values" >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed or not on PATH" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose v2 is not available" >&2
  exit 1
fi

COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

if [[ -z "$BASE_URL" ]]; then
  BASE_URL="http://127.0.0.1"
fi

guard_against_trust_node_edge_conflict() {
  if [[ "$COMPOSE_FILE" == "deploy/production/docker-compose.production.yml" ]] && docker ps --format '{{.Names}}' | grep -Fxq "production-nginx-1"; then
    cat >&2 <<'EOF'
production-nginx-1 is already running and owns host ports 80/443.
That is the HTTPS trust-node edge from docker-compose.trust-node.yml.

Do not start docker-compose.production.yml on this host unless you intend to
replace the trust-node edge with the HTTP-only pilot Caddy edge.

For the live afritechnology.com trust node, use:
  ./scripts/setup_production_trust_node.sh --repair-cert
  ./scripts/go_live_anchor_now.sh --profile sepolia --skip-anchor
EOF
    exit 1
  fi
}

wait_for_api() {
  echo "==> Waiting for afritech-api health"
  for attempt in {1..60}; do
    if "${COMPOSE[@]}" exec -T afritech-api python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" >/dev/null 2>&1; then
      return 0
    fi
    if [[ "$attempt" -eq 60 ]]; then
      echo "afritech-api did not become healthy" >&2
      "${COMPOSE[@]}" ps >&2
      "${COMPOSE[@]}" logs --tail=120 afritech-api >&2
      exit 1
    fi
    sleep 2
  done
}

guard_against_trust_node_edge_conflict

echo "==> Validating compose configuration"
"${COMPOSE[@]}" config --quiet

echo "==> Updating afritech-api"
"${COMPOSE[@]}" up -d --no-deps --build afritech-api
wait_for_api

echo "==> Updating afritech-dashboard"
"${COMPOSE[@]}" up -d --no-deps --build afritech-dashboard

echo "==> Updating edge"
"${COMPOSE[@]}" up -d --no-deps edge
"${COMPOSE[@]}" exec -T edge caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
"${COMPOSE[@]}" exec -T edge caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile

echo "==> Compose status"
"${COMPOSE[@]}" ps

echo "==> Running production probe against $BASE_URL"
./scripts/run_local_production_probe.sh "$BASE_URL"

echo "Zero-downtime production deployment completed."
