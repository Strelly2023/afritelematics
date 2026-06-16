#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-deploy/production/docker-compose.trust-node.yml}"
ENV_FILE="${ENV_FILE:-deploy/production/.env.production.trust-node}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "missing env file: $ENV_FILE" >&2
  exit 1
fi

DOMAIN="$(awk -F= '$1 == "AFRITECH_DOMAIN" { print $2 }' "$ENV_FILE" | tail -n 1)"
if [[ -z "$DOMAIN" ]]; then
  echo "AFRITECH_DOMAIN is required in $ENV_FILE" >&2
  exit 1
fi

COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

echo "==> Building dashboard image"
"${COMPOSE[@]}" build afritech-dashboard

echo "==> Launching API, dashboard, and Nginx edge"
"${COMPOSE[@]}" up -d afritech-api afritech-dashboard nginx

echo "==> Dashboard routes"
echo "Operator dashboard: https://$DOMAIN/"
echo "Feature registry portal: https://$DOMAIN/public/feature-registry/portal"
echo "Global verification portal: https://$DOMAIN/public/global-verification/portal"
echo "Ecosystem trust portal: https://$DOMAIN/public/ecosystem-evolution/portal"
