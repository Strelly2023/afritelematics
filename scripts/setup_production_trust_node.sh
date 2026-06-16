#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="deploy/production/docker-compose.trust-node.yml"
ENV_FILE="deploy/production/.env.production.trust-node"
ISSUE_CERT=0
APPLY_FIREWALL=0
NO_CACHE=0

usage() {
  cat <<'EOF'
usage: ./scripts/setup_production_trust_node.sh [--issue-cert] [--apply-firewall] [--no-cache]

Builds and launches the production trust node using Nginx, HTTPS-ready
Let's Encrypt wiring, the operator dashboard, public verification endpoints,
and live-anchor-capable API services.

Before running:
  cp deploy/production/.env.production.trust-node.example deploy/production/.env.production.trust-node
  replace every placeholder
  place secrets in deploy/production/secrets/
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --issue-cert)
      ISSUE_CERT=1
      shift
      ;;
    --apply-firewall)
      APPLY_FIREWALL=1
      shift
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

if [[ ! -f "$ENV_FILE" ]]; then
  echo "missing env file: $ENV_FILE" >&2
  echo "copy deploy/production/.env.production.trust-node.example and replace placeholders" >&2
  exit 1
fi

if grep -Eq 'replace-with|your-domain\.example|trust\.afritech\.example|YOUR_' "$ENV_FILE"; then
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

DOMAIN="$(awk -F= '$1 == "AFRITECH_DOMAIN" { print $2 }' "$ENV_FILE" | tail -n 1)"
EMAIL="$(awk -F= '$1 == "AFRITECH_TLS_EMAIL" { print $2 }' "$ENV_FILE" | tail -n 1)"
if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
  echo "AFRITECH_DOMAIN and AFRITECH_TLS_EMAIL are required" >&2
  exit 1
fi
CERT_DOMAINS=("$DOMAIN" "app.$DOMAIN" "api.$DOMAIN" "verify.$DOMAIN")

if [[ "$APPLY_FIREWALL" -eq 1 ]]; then
  if ! command -v ufw >/dev/null 2>&1; then
    echo "ufw is not installed; install it or omit --apply-firewall" >&2
    exit 1
  fi
  sudo ufw allow OpenSSH
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw --force enable
fi

COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$(basename "$(dirname "$COMPOSE_FILE")")}"
BUILD_ARGS=()
if [[ "$NO_CACHE" -eq 1 ]]; then
  BUILD_ARGS+=(--no-cache)
fi

ensure_compose_volume() {
  local volume_name="$1"

  if docker volume inspect "$volume_name" >/dev/null 2>&1; then
    return 0
  fi

  docker volume create "$volume_name" >/dev/null
}

echo "==> Validating trust-node compose configuration"
"${COMPOSE[@]}" config --quiet

echo "==> Building trust-node images"
"${COMPOSE[@]}" build "${BUILD_ARGS[@]}"

if [[ "$ISSUE_CERT" -eq 1 ]]; then
  echo "==> Creating temporary certificate for Nginx bootstrap"
  TMP_DIR="$(mktemp -d)"
  mkdir -p "$TMP_DIR/live/$DOMAIN"
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "$TMP_DIR/live/$DOMAIN/privkey.pem" \
    -out "$TMP_DIR/live/$DOMAIN/fullchain.pem" \
    -subj "/CN=$DOMAIN" >/dev/null 2>&1

  CERT_VOLUME="${PROJECT_NAME}_certbot_certs"
  ensure_compose_volume "$CERT_VOLUME"
  docker run --rm -v "$CERT_VOLUME:/etc/letsencrypt" -v "$TMP_DIR:/tmp/certs:ro" alpine \
    sh -c "mkdir -p /etc/letsencrypt/live/$DOMAIN && cp /tmp/certs/live/$DOMAIN/* /etc/letsencrypt/live/$DOMAIN/"

  echo "==> Starting Nginx for ACME challenge"
  "${COMPOSE[@]}" up -d nginx

  CERTBOT_DOMAIN_ARGS=()
  for cert_domain in "${CERT_DOMAINS[@]}"; do
    CERTBOT_DOMAIN_ARGS+=(-d "$cert_domain")
  done

  echo "==> Requesting Let's Encrypt certificate for ${CERT_DOMAINS[*]}"
  "${COMPOSE[@]}" --profile certbot run --rm certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --non-interactive \
    --expand \
    "${CERTBOT_DOMAIN_ARGS[@]}"

  echo "==> Reloading Nginx with issued certificate"
  "${COMPOSE[@]}" exec -T nginx nginx -s reload
else
  echo "==> Starting trust-node stack without issuing a new certificate"
  "${COMPOSE[@]}" up -d --remove-orphans
fi

echo "==> Waiting for API health"
for attempt in {1..30}; do
  if "${COMPOSE[@]}" exec -T afritech-api python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()" >/dev/null 2>&1; then
    break
  fi
  if [[ "$attempt" -eq 30 ]]; then
    "${COMPOSE[@]}" logs --tail=120 afritech-api >&2
    exit 1
  fi
  sleep 2
done

"${COMPOSE[@]}" ps
./scripts/run_local_production_probe.sh "https://$DOMAIN"
echo "Production trust node launched at https://$DOMAIN"
