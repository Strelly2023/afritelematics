#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="deploy/production/docker-compose.trust-node.yml"
ENV_FILE="deploy/production/.env.production.trust-node"
ISSUE_CERT=0
APPLY_FIREWALL=0
NO_CACHE=0
REPAIR_CERT=0

usage() {
  cat <<'EOF'
usage: ./scripts/setup_production_trust_node.sh [--issue-cert] [--repair-cert] [--apply-firewall] [--no-cache]

Builds and launches the production trust node using Nginx, HTTPS-ready
Let's Encrypt wiring, the operator dashboard, public verification endpoints,
and live-anchor-capable API services.

Before running:
  cp deploy/production/.env.production.trust-node.example deploy/production/.env.production.trust-node
  replace every placeholder
  place secrets in deploy/production/secrets/

Use --repair-cert when HTTPS is serving the temporary bootstrap certificate
after Certbot reports that an existing certificate is not yet due for renewal.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --issue-cert)
      ISSUE_CERT=1
      shift
      ;;
    --repair-cert)
      REPAIR_CERT=1
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

canonical_cert_exists() {
  local cert_volume="$1"

  docker run --rm -v "$cert_volume:/etc/letsencrypt" nginx:1.27-alpine \
    sh -c 'test -s "/etc/letsencrypt/live/$1/fullchain.pem" && test -s "/etc/letsencrypt/live/$1/privkey.pem"' \
    _ "$DOMAIN" >/dev/null 2>&1
}

valid_canonical_cert_exists() {
  local cert_volume="$1"

  docker run --rm -v "$cert_volume:/etc/letsencrypt" nginx:1.27-alpine \
    sh -c '
      domain="$1"
      shift
      fullchain="/etc/letsencrypt/live/$domain/fullchain.pem"

      [ -s "$fullchain" ] || exit 1
      openssl x509 -in "$fullchain" -noout -checkend 0 >/dev/null 2>&1 || exit 1
      names="$(openssl x509 -in "$fullchain" -noout -ext subjectAltName 2>/dev/null || true)"

      for required in "$@"; do
        echo "$names" | grep -Fq "DNS:$required" || exit 1
      done
    ' _ "$DOMAIN" "${CERT_DOMAINS[@]}" >/dev/null 2>&1
}

repoint_canonical_cert() {
  local cert_volume="$1"

  docker run --rm -v "$cert_volume:/etc/letsencrypt" nginx:1.27-alpine \
    sh -c '
      domain="$1"
      shift
      best=""

      for fullchain in /etc/letsencrypt/live/"$domain"*/fullchain.pem; do
        [ -e "$fullchain" ] || continue

        cert_dir="$(dirname "$fullchain")"
        cert_name="$(basename "$cert_dir")"
        if ! openssl x509 -in "$fullchain" -noout -checkend 0 >/dev/null 2>&1; then
          continue
        fi

        names="$(openssl x509 -in "$fullchain" -noout -ext subjectAltName 2>/dev/null || true)"
        ok=1
        for required in "$@"; do
          echo "$names" | grep -Fq "DNS:$required" || ok=0
        done

        if [ "$ok" = 1 ]; then
          best="$cert_name"
          break
        fi
      done

      if [ -n "$best" ] && [ "$best" != "$domain" ]; then
        rm -rf "/etc/letsencrypt/live/$domain"
        ln -s "$best" "/etc/letsencrypt/live/$domain"
        echo "Using certificate lineage $best via live/$domain"
      elif [ -n "$best" ]; then
        echo "Using certificate lineage $best"
      fi
    ' _ "$DOMAIN" "${CERT_DOMAINS[@]}"
}

repair_active_cert() {
  local cert_volume="$1"

  repoint_canonical_cert "$cert_volume"
  if ! valid_canonical_cert_exists "$cert_volume"; then
    echo "No valid Let's Encrypt certificate found for ${CERT_DOMAINS[*]} in volume $cert_volume" >&2
    echo "Run again with --issue-cert after confirming DNS points to this host." >&2
    exit 1
  fi

  echo "==> Recreating Nginx with repaired certificate mount"
  "${COMPOSE[@]}" up -d --force-recreate nginx
  echo "==> Active TLS certificate"
  "${COMPOSE[@]}" exec -T nginx sh -c "openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -noout -subject -issuer -ext subjectAltName"
}

CERT_VOLUME="${PROJECT_NAME}_certbot_certs"
ensure_compose_volume "$CERT_VOLUME"

if [[ "$REPAIR_CERT" -eq 1 ]]; then
  repair_active_cert "$CERT_VOLUME"
  exit 0
fi

echo "==> Validating trust-node compose configuration"
"${COMPOSE[@]}" config --quiet

echo "==> Building trust-node images"
"${COMPOSE[@]}" build "${BUILD_ARGS[@]}"

if [[ "$ISSUE_CERT" -eq 1 ]]; then
  repoint_canonical_cert "$CERT_VOLUME"
  CERTBOT_NEEDED=1

  if valid_canonical_cert_exists "$CERT_VOLUME"; then
    CERTBOT_NEEDED=0
  fi

  if canonical_cert_exists "$CERT_VOLUME"; then
    echo "==> Reusing existing certificate path for Nginx bootstrap"
  else
    echo "==> Creating temporary certificate for Nginx bootstrap"
    TMP_DIR="$(mktemp -d)"
    mkdir -p "$TMP_DIR/live/$DOMAIN"
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
      -keyout "$TMP_DIR/live/$DOMAIN/privkey.pem" \
      -out "$TMP_DIR/live/$DOMAIN/fullchain.pem" \
      -subj "/CN=$DOMAIN" >/dev/null 2>&1

    docker run --rm -v "$CERT_VOLUME:/etc/letsencrypt" -v "$TMP_DIR:/tmp/certs:ro" alpine \
      sh -c "mkdir -p /etc/letsencrypt/live/$DOMAIN && cp /tmp/certs/live/$DOMAIN/* /etc/letsencrypt/live/$DOMAIN/"
  fi

  echo "==> Starting Nginx for ACME challenge"
  "${COMPOSE[@]}" up -d nginx

  if [[ "$CERTBOT_NEEDED" -eq 1 ]]; then
    CERTBOT_DOMAIN_ARGS=()
    for cert_domain in "${CERT_DOMAINS[@]}"; do
      CERTBOT_DOMAIN_ARGS+=(-d "$cert_domain")
    done

    echo "==> Requesting Let's Encrypt certificate for ${CERT_DOMAINS[*]}"
    "${COMPOSE[@]}" --profile certbot run --rm certbot certonly \
      --webroot \
      --webroot-path /var/www/certbot \
      --email "$EMAIL" \
      --cert-name "$DOMAIN" \
      --agree-tos \
      --no-eff-email \
      --non-interactive \
      --expand \
      "${CERTBOT_DOMAIN_ARGS[@]}"

    repoint_canonical_cert "$CERT_VOLUME"
  else
    echo "==> Existing Let's Encrypt certificate already covers ${CERT_DOMAINS[*]}"
  fi

  echo "==> Reloading Nginx with active certificate"
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
