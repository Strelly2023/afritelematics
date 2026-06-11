#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="deploy/production/docker-compose.production.yml"
ENV_FILE="deploy/production/.env.production"
BASE_URL=""
NO_CACHE=0

usage() {
  cat <<'EOF'
usage: ./scripts/deploy_production_compose.sh [--base-url https://<domain>] [--no-cache]

Builds and updates the production Docker Compose stack without taking the
current stack down first. The script fails on missing production config,
placeholder secrets, failed builds, unhealthy services, or failed probes.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url)
      BASE_URL="${2:-}"
      if [[ -z "$BASE_URL" ]]; then
        echo "--base-url requires a value" >&2
        exit 1
      fi
      shift 2
      ;;
    --no-cache)
      NO_CACHE=1
      shift
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
  echo "missing production env file: $ENV_FILE" >&2
  echo "copy deploy/production/.env.production.example and replace every placeholder" >&2
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
BUILD_ARGS=()
if [[ "$NO_CACHE" -eq 1 ]]; then
  BUILD_ARGS+=(--no-cache)
fi

if [[ -z "$BASE_URL" ]]; then
  DOMAIN="$(awk -F= '$1 == "AFRITECH_DOMAIN" { print $2 }' "$ENV_FILE" | tail -n 1)"
  if [[ -n "$DOMAIN" ]]; then
    BASE_URL="https://$DOMAIN"
  fi
fi

echo "==> Validating compose configuration"
"${COMPOSE[@]}" config --quiet

echo "==> Building images before replacing running containers"
"${COMPOSE[@]}" build "${BUILD_ARGS[@]}"

echo "==> Starting updated stack"
"${COMPOSE[@]}" up -d --remove-orphans

echo "==> Waiting for afritech-api health"
for attempt in {1..30}; do
  if "${COMPOSE[@]}" exec -T afritech-api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" >/dev/null 2>&1; then
    break
  fi

  if [[ "$attempt" -eq 30 ]]; then
    echo "afritech-api did not become healthy" >&2
    "${COMPOSE[@]}" ps >&2
    "${COMPOSE[@]}" logs --tail=120 afritech-api >&2
    exit 1
  fi

  sleep 2
done

echo "==> Compose status"
"${COMPOSE[@]}" ps

if [[ -n "$BASE_URL" ]]; then
  echo "==> Running production probe against $BASE_URL"
  ./scripts/run_local_production_probe.sh "$BASE_URL"
else
  echo "No base URL detected; run ./scripts/run_local_production_probe.sh https://<domain> manually."
fi

echo "Production compose deployment completed."
