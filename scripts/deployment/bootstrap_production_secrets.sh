#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SECRETS_DIR="${SECRETS_DIR:-$ROOT_DIR/deploy/production/secrets}"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/deploy/production/.env.production.trust-node}"
ROTATE="${ROTATE:-false}"
BOOTSTRAP_TLSDIR="${BOOTSTRAP_TLSDIR:-$ROOT_DIR/.tmp/production-cert-bootstrap}"
DOMAIN="${AFRITECH_DOMAIN:-localhost}"

umask 077

log() {
  printf '%s\n' "$*" >&2
}

fingerprint_pem() {
  openssl pkey -in "$1" -pubout -outform PEM | openssl pkey -pubin -outform DER | shasum -a 256 | awk '{print $1}'
}

ensure_ignored() {
  git -C "$ROOT_DIR" check-ignore "$@" >/dev/null
}

ensure_dir() {
  mkdir -p "$1"
  chmod 700 "$1"
}

generate_rsa_pair() {
  local private_key="$SECRETS_DIR/afritech_private_key.pem"
  local public_key="$SECRETS_DIR/afritech_public_key.pem"

  if [[ -f "$private_key" || -f "$public_key" ]]; then
    if [[ -f "$private_key" && -f "$public_key" && "$ROTATE" != "true" ]]; then
      log "afritech RSA signing key already exists; leaving in place"
      return 0
    fi
    if [[ "$ROTATE" != "true" ]]; then
      log "partial afritech RSA signing key material exists; set ROTATE=true to replace"
      return 1
    fi
  fi

  log "generating RSA 4096 signing key pair"
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out "$private_key" >/dev/null 2>&1
  openssl pkey -in "$private_key" -pubout -out "$public_key" >/dev/null 2>&1
  chmod 600 "$private_key"
  chmod 644 "$public_key"

  openssl pkey -in "$private_key" -check -noout >/dev/null 2>&1
  openssl pkey -pubin -in "$public_key" -text -noout >/dev/null 2>&1
}

generate_eth_key() {
  local eth_key="$SECRETS_DIR/eth_private_key"
  if [[ -f "$eth_key" && "$ROTATE" != "true" ]]; then
    log "eth private key already exists; leaving in place"
    return 0
  fi

  local key_hex
  key_hex="$(openssl rand -hex 32)"
  printf '0x%s\n' "$key_hex" > "$eth_key"
  chmod 600 "$eth_key"
  if ! grep -Eq '^0x[0-9a-fA-F]{64}$' "$eth_key"; then
    log "generated eth key has invalid format"
    return 1
  fi
}

generate_trust_seed() {
  local trust_seed_file="$SECRETS_DIR/novatrust_ed25519_private_key.b64"
  if [[ -f "$trust_seed_file" && "$ROTATE" != "true" ]]; then
    log "NovaTrust Ed25519 seed already exists; leaving in place"
    return 0
  fi
  python3 - <<'PY' > "$trust_seed_file"
import base64, os
print(base64.b64encode(os.urandom(32)).decode("ascii"))
PY
  chmod 600 "$trust_seed_file"
  if ! python3 - <<'PY' "$trust_seed_file" >/dev/null 2>&1; then
import base64, pathlib, sys
raw = base64.b64decode(pathlib.Path(sys.argv[1]).read_text().strip())
assert len(raw) == 32
PY
    log "invalid NovaTrust Ed25519 seed"
    return 1
  fi
}

generate_api_contract_seed() {
  local api_seed_file="$SECRETS_DIR/novatech_api_contract_signing_private_key.b64"
  if [[ -f "$api_seed_file" && "$ROTATE" != "true" ]]; then
    log "API contract Ed25519 seed already exists; leaving in place"
    return 0
  fi
  python3 - <<'PY' > "$api_seed_file"
import base64, os
print(base64.b64encode(os.urandom(32)).decode("ascii"))
PY
  chmod 600 "$api_seed_file"
}

generate_bootstrap_tls() {
  local fullchain_dir="$BOOTSTRAP_TLSDIR/live/$DOMAIN"
  local fullchain="$fullchain_dir/fullchain.pem"
  local privkey="$fullchain_dir/privkey.pem"
  if [[ -s "$fullchain" && -s "$privkey" && "$ROTATE" != "true" ]]; then
    log "bootstrap TLS certificate already exists; leaving in place"
    bootstrap_tls_volume "$fullchain_dir"
    return 0
  fi

  ensure_dir "$BOOTSTRAP_TLSDIR"
  mkdir -p "$fullchain_dir"
  local san_list="DNS:$DOMAIN,DNS:www.$DOMAIN,DNS:app.$DOMAIN,DNS:api.$DOMAIN,DNS:novacodepro.$DOMAIN,DNS:trust.$DOMAIN,DNS:status.$DOMAIN,DNS:verify.$DOMAIN,DNS:developer.$DOMAIN,DNS:docs.$DOMAIN,DNS:sdk.$DOMAIN,DNS:events.$DOMAIN,DNS:gateway.$DOMAIN,DNS:support.$DOMAIN,DNS:download.$DOMAIN,DNS:business.$DOMAIN,DNS:merchant.$DOMAIN,DNS:agent.$DOMAIN,DNS:operator.$DOMAIN,IP:127.0.0.1"
  openssl req -x509 -nodes -newkey rsa:2048 -days 30 \
    -keyout "$privkey" \
    -out "$fullchain" \
    -subj "/CN=$DOMAIN" \
    -addext "subjectAltName=$san_list" >/dev/null 2>&1
  chmod 600 "$privkey"
  chmod 644 "$fullchain"
  bootstrap_tls_volume "$fullchain_dir"
}

bootstrap_tls_volume() {
  local fullchain_dir="$1"
  if ! command -v docker >/dev/null 2>&1; then
    log "docker not available; bootstrap TLS remains on disk only"
    return 0
  fi

  local project_names=("${COMPOSE_PROJECT_NAME:-production}")
  local repo_project
  repo_project="$(basename "$ROOT_DIR")"
  if [[ "${project_names[0]}" != "$repo_project" ]]; then
    project_names+=("$repo_project")
  fi

  for project_name in "${project_names[@]}"; do
    local cert_volume="${project_name}_certbot_certs"
    docker volume create "$cert_volume" >/dev/null
    docker run --rm \
      -v "$cert_volume:/etc/letsencrypt" \
      -v "$BOOTSTRAP_TLSDIR:/bootstrap:ro" \
      alpine:3.20 \
      sh -c "mkdir -p /etc/letsencrypt/live/$DOMAIN && cp -f /bootstrap/live/$DOMAIN/fullchain.pem /etc/letsencrypt/live/$DOMAIN/fullchain.pem && cp -f /bootstrap/live/$DOMAIN/privkey.pem /etc/letsencrypt/live/$DOMAIN/privkey.pem && chmod 644 /etc/letsencrypt/live/$DOMAIN/fullchain.pem && chmod 600 /etc/letsencrypt/live/$DOMAIN/privkey.pem"
  done
}

generate_env_file() {
  local postgres_password jwt_secret event_secret afriride_secret django_secret audit_key grafana_pw chain_address chain_contract chain_rpc chain_ws chain_rpc_base chain_ws_base novatrust_seed api_contract_seed
  postgres_password="$(openssl rand -hex 18)"
  jwt_secret="$(openssl rand -hex 32)"
  event_secret="$(openssl rand -hex 32)"
  afriride_secret="$(openssl rand -hex 32)"
  django_secret="$(openssl rand -hex 32)"
  audit_key="$(openssl rand -hex 32)"
  grafana_pw="$(openssl rand -base64 18 | tr -d '=+/')"
  chain_address="0x$(openssl rand -hex 20)"
  chain_contract="0x$(openssl rand -hex 20)"
  chain_rpc="http://127.0.0.1:8545"
  chain_ws="ws://127.0.0.1:8546"
  chain_rpc_base="http://127.0.0.1:28545"
  chain_ws_base="ws://127.0.0.1:28546"
  novatrust_seed="$(python3 - <<'PY'
import base64, os
print(base64.b64encode(os.urandom(32)).decode("ascii"))
PY
)"
  api_contract_seed="$(python3 - <<'PY'
import base64, os
print(base64.b64encode(os.urandom(32)).decode("ascii"))
PY
)"

  cat > "$ENV_FILE" <<EOF
AFRITECH_DOMAIN=$DOMAIN
AFRITECH_TLS_EMAIL=ops@$DOMAIN
AFRITECH_ENV=production
AFRITECH_RUNTIME_ENVIRONMENT=production
AFRITECH_OTEL_ENABLED=true
AFRITECH_ALLOW_PILOT_TOKEN_ISSUANCE=false
AFRITECH_AUTH_BOOTSTRAP_SECRET=$jwt_secret
AFRITECH_EVENT_INGESTION_SECRET=$event_secret
AFRIRIDE_JWT_SECRET=$afriride_secret
AFRIRIDE_EVENT_INGESTION_SECRET=$(openssl rand -hex 32)
AFRIRIDE_DJANGO_SECRET_KEY=$django_secret
AFRIRIDE_AUDIT_API_KEY=$audit_key
DATABASE_URL=postgresql://afritech:$postgres_password@postgres:5432/afritech
NOVATECH_POSTGRES_DSN=postgresql://afritech:$postgres_password@postgres:5432/afritech
NOVACODEPRO_DATABASE_URL=postgresql://afritech:$postgres_password@postgres:5432/afritech
NOVATECH_REDIS_DSN=redis://redis:6379/0
NOVATECH_EVENT_BROKER_DSN=kafka:9092
NOVATECH_ALLOW_MEMORY_FALLBACK=false
NOVATECH_PRODUCT_RUNTIME_ENABLED=true
NOVATECH_REGISTRY_WRITES_ENABLED=true
NOVATRUST_ED25519_PRIVATE_KEY_B64=$novatrust_seed
NOVATRUST_SIGNING_KEY_ID=novatrust-prod-local-001
NOVATRUST_KEY_ROTATION_ENABLED=true
NOVATRUST_KEY_ROTATION_DAYS=90
NOVATECH_API_CONTRACT_SIGNING_PRIVATE_KEY_B64=$api_contract_seed
NOVATECH_API_CONTRACT_SIGNING_KEY_ID=novatech-api-contract-local-001
POSTGRES_DB=afritech
POSTGRES_USER=afritech
POSTGRES_PASSWORD=$postgres_password
REDIS_URL=redis://redis:6379/0
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
AFRITECH_SIGNING_PRIVATE_KEY_PATH=/run/secrets/afritech_private_key.pem
AFRITECH_SIGNING_PUBLIC_KEY_PATH=/run/secrets/afritech_public_key.pem
AFRITECH_CHAIN_MODE=sepolia
AFRITECH_CHAIN_NETWORK=sepolia
AFRITECH_CHAIN_RPC_URL_SEPOLIA=$chain_rpc
AFRITECH_CHAIN_WS_URL_SEPOLIA=$chain_ws
AFRITECH_CHAIN_RPC_URL_BASE_SEPOLIA=$chain_rpc_base
AFRITECH_CHAIN_WS_URL_BASE_SEPOLIA=$chain_ws_base
AFRITECH_CHAIN_RPC_URL_MAINNET=https://mainnet.invalid
AFRITECH_CHAIN_WS_URL_MAINNET=wss://mainnet.invalid
AFRITECH_CHAIN_PRIVATE_KEY_PATH=/run/secrets/eth_private_key
AFRITECH_CHAIN_ADDRESS_CHECKSUM=$chain_address
AFRITECH_CHAIN_ID=11155111
AFRITECH_CHAIN_CONTRACT_ADDRESS=$chain_contract
AFRITECH_CHAIN_ENABLE_PUBLISH=false
AFRITECH_CHAIN_AUTO_PUBLISH_ON_PROOF=false
AFRITECH_CHAIN_ETHERSCAN_VERIFIED=false
AFRITECH_CHAIN_INDEX_BACKEND=file
AFRITECH_CHAIN_INDEX_FILE=/var/lib/afritech/anchor-index.json
AFRITECH_ECOSYSTEM_LIVE_RECEIPT_FILE=/var/lib/afritech/ecosystem-live-anchor.json
AFRITECH_CHAIN_EVENT_SUBSCRIBER_ENABLED=true
AFRITECH_CHAIN_EVENT_SUBSCRIBER_TRANSPORT=websocket
AFRITECH_CHAIN_EVENT_BACKFILL_ENABLED=false
AFRITECH_CHAIN_EVENT_RECONNECT_DELAY_SECONDS=5
AFRITECH_CHAIN_CONTRACT_DEPLOYMENT_BLOCK=1
AFRITECH_CHAIN_TX_TIMEOUT=120
AFRITECH_CHAIN_GAS_PRICE_GWEI=2
VITE_AFRIRIDE_API_URL=https://api.$DOMAIN
VITE_AFRIRIDE_APP_VERSION=trust-node-local
VITE_AFRITECH_PUBLIC_API_URL=https://api.$DOMAIN
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=$grafana_pw
POSTGRES_EXPORTER_DATA_SOURCE_NAME=postgresql://afritech:$postgres_password@postgres:5432/afritech?sslmode=disable
NOVARIDE_ENVIRONMENT=production
NOVARIDE_REGION=AU
NOVARIDE_AVAILABILITY_ZONE=local-a
NOVARIDE_PERSISTENCE_ADAPTER=postgresql
NOVARIDE_EVENT_FABRIC_ADAPTER=kafka_outbox
NOVARIDE_POSTGRES_DSN=postgresql://afritech:$postgres_password@postgres:5432/afritech
NOVARIDE_REDIS_DSN=redis://redis:6379/1
NOVARIDE_KAFKA_BOOTSTRAP_SERVERS=kafka:9092
NOVARIDE_KAFKA_SECURITY_PROTOCOL=PLAINTEXT
NOVARIDE_EVIDENCE_SIGNING_KEY_REF=/run/secrets/afritech_private_key.pem
NOVARIDE_METRICS_ENABLED=true
NOVARIDE_OTEL_ENDPOINT=http://otel-collector:4318
NOVARIDE_ALERT_WEBHOOK_REF=
NOVARIDE_REAL_PAYMENTS_ENABLED=false
NOVARIDE_GA_ALLOWED=false
NOVARIDE_PROVIDER_PROBE_INTERVAL_SECONDS=30
NOVARIDE_PROVIDER_PROBE_TIMEOUT_SECONDS=2.0
NOVARIDE_OUTBOX_BATCH_SIZE=100
NOVARIDE_OUTBOX_POLL_INTERVAL_SECONDS=1.0
NOVARIDE_SYNC_BATCH_MAX_OPERATIONS=100
NOVARIDE_SYNC_PAYLOAD_MAX_BYTES=256000
NOVARIDE_RETENTION_OFFLINE_OPERATIONS_DAYS=30
NOVARIDE_RETENTION_EVIDENCE_DAYS=365
NOVAID_PERSISTENCE_BACKEND=postgres
NOVAID_DATABASE_URL=postgresql://afritech:$postgres_password@postgres:5432/afritech
NOVAID_REDIS_URL=redis://redis:6379/0
NOVAID_REDIS_REQUIRED=true
NOVAID_WEBAUTHN_REDIS_REQUIRED=true
NOVAID_JWT_ISSUER=https://$DOMAIN
NOVAID_JWT_AUDIENCE=$DOMAIN-clients
NOVAID_SIGNING_KEY=controlled-pilot-novaid-signing-key-00001
NOVAID_WEBAUTHN_RP_ID=$DOMAIN
NOVAID_WEBAUTHN_RP_NAME=NovaID
NOVAID_WEBAUTHN_ORIGINS=https://$DOMAIN,https://api.$DOMAIN,https://novacodepro.$DOMAIN
NOVAID_WEBAUTHN_REQUIRE_UV=true
NOVAID_WEBAUTHN_ATTESTATION=none
NOVAID_SERVICE_INSTANCE_ID=novaid-local
NOVAID_INSTANCE_ID=novaid-local
NOVAID_TRACE_EXPORT_PATH=/var/lib/afritech/novaid-traces.jsonl
NOVACODEPRO_EVENT_BUS_KAFKA_BROKERS=kafka:9092
NOVACODEPRO_AGENT_ASYNC_EXECUTION=true
EOF

  chmod 600 "$ENV_FILE"
}

main() {
  ensure_dir "$SECRETS_DIR"
  generate_rsa_pair
  generate_eth_key
  generate_trust_seed
  generate_api_contract_seed
  generate_bootstrap_tls
  if [[ ! -f "$ENV_FILE" || "$ROTATE" == "true" ]]; then
    generate_env_file
  fi

  ensure_ignored \
    deploy/production/secrets/eth_private_key \
    deploy/production/secrets/afritech_private_key.pem \
    deploy/production/secrets/afritech_public_key.pem \
    deploy/production/secrets/novatrust_ed25519_private_key.b64 \
    deploy/production/secrets/novatech_api_contract_signing_private_key.b64 \
    deploy/production/.env.production.trust-node

  log "secret bootstrap complete"
  log "RSA fingerprint: $(fingerprint_pem "$SECRETS_DIR/afritech_private_key.pem")"
  log "ETH key: $(shasum -a 256 "$SECRETS_DIR/eth_private_key" | awk '{print $1}')"
}

main "$@"
