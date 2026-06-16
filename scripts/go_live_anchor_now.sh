#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-deploy/production/docker-compose.trust-node.yml}"
ENV_FILE="${ENV_FILE:-deploy/production/.env.production.trust-node}"
PROFILE="sepolia"
ISSUE_CERT=1
APPLY_FIREWALL=1
SKIP_DEPLOY=0
SKIP_ANCHOR=0

usage() {
  cat <<'EOF'
usage: ./scripts/go_live_anchor_now.sh [--profile sepolia|base-sepolia|mainnet] [--skip-deploy] [--skip-anchor] [--no-cert] [--no-firewall]

Runs the production trust-node go-live sequence:
  1. verify env, DNS, and secrets
  2. deploy Nginx + HTTPS + API + dashboard
  3. open public ecosystem verification access
  4. launch dashboard
  5. publish a live ecosystem anchor
  6. re-check public verification endpoints

The script fails closed on placeholder config, missing secrets, failed TLS/API
probes, failed chain readiness, or a non-live anchor receipt.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="${2:-}"
      if [[ -z "$PROFILE" ]]; then
        echo "--profile requires a value" >&2
        exit 1
      fi
      shift 2
      ;;
    --skip-deploy)
      SKIP_DEPLOY=1
      shift
      ;;
    --skip-anchor)
      SKIP_ANCHOR=1
      shift
      ;;
    --no-cert)
      ISSUE_CERT=0
      shift
      ;;
    --no-firewall)
      APPLY_FIREWALL=0
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
  exit 1
fi

if grep -Eq 'replace-with|your-domain\.example|trust\.afritech\.example|YOUR_|example\.invalid' "$ENV_FILE"; then
  echo "$ENV_FILE still contains placeholder values" >&2
  exit 1
fi

DOMAIN="$(awk -F= '$1 == "AFRITECH_DOMAIN" { print $2 }' "$ENV_FILE" | tail -n 1)"
if [[ -z "$DOMAIN" ]]; then
  echo "AFRITECH_DOMAIN is required in $ENV_FILE" >&2
  exit 1
fi

echo "==> Checking DNS for $DOMAIN"
python3 - "$DOMAIN" <<'PY'
import socket
import sys

domain = sys.argv[1]
try:
    addresses = sorted(set(socket.gethostbyname_ex(domain)[2]))
except Exception as exc:
    raise SystemExit(f"DNS resolution failed for {domain}: {exc}")
if not addresses:
    raise SystemExit(f"DNS resolution returned no A records for {domain}")
print(f"DNS OK: {domain} -> {', '.join(addresses)}")
PY

for secret in \
  deploy/production/secrets/eth_private_key \
  deploy/production/secrets/afritech_private_key.pem \
  deploy/production/secrets/afritech_public_key.pem
do
  if [[ ! -s "$secret" ]]; then
    echo "missing or empty secret: $secret" >&2
    exit 1
  fi
done

SETUP_ARGS=()
if [[ "$ISSUE_CERT" -eq 1 ]]; then
  SETUP_ARGS+=(--issue-cert)
fi
if [[ "$APPLY_FIREWALL" -eq 1 ]]; then
  SETUP_ARGS+=(--apply-firewall)
fi

BASE_URL="https://$DOMAIN"

if [[ "$SKIP_DEPLOY" -eq 0 ]]; then
  echo "==> Go live: deploying production trust node"
  ./scripts/setup_production_trust_node.sh "${SETUP_ARGS[@]}"
fi

echo "==> Launching trust dashboard"
COMPOSE_FILE="$COMPOSE_FILE" ENV_FILE="$ENV_FILE" ./scripts/launch_trust_dashboard.sh

echo "==> Opening ecosystem access"
./scripts/open_ecosystem_access.sh "$BASE_URL"

if [[ "$SKIP_ANCHOR" -eq 0 ]]; then
  echo "==> Anchor now: publishing live public-ledger receipt on $PROFILE"
  COMPOSE_FILE="$COMPOSE_FILE" ENV_FILE="$ENV_FILE" ./scripts/enable_live_anchoring.sh "$PROFILE"
fi

echo "==> Final public probe"
./scripts/run_local_production_probe.sh "$BASE_URL"

echo "LIVE TRUST NODE READY"
echo "Dashboard: $BASE_URL/"
echo "Ecosystem portal: $BASE_URL/public/ecosystem-evolution/portal"
echo "Ecosystem verification: $BASE_URL/public/ecosystem-evolution/verify"
