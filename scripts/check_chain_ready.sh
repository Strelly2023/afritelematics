#!/usr/bin/env bash

set -e

COMPOSE_FILE="deploy/production/docker-compose.production.yml"

echo "========================================="
echo " AfriTech Blockchain Readiness Check"
echo "========================================="

# =========================
# ✅ CHECK CONTAINER
# =========================
echo ""
echo "==> Checking afritech-api container"

if ! docker compose -f "$COMPOSE_FILE" ps | grep -q "afritech-api.*Up"; then
  echo "❌ afritech-api container is not running"
  exit 1
fi

echo "✅ afritech-api is running"

# =========================
# ✅ CHECK ENV VARIABLES
# =========================
echo ""
echo "==> Checking required environment variables"

ENV_OUTPUT=$(docker compose -f "$COMPOSE_FILE" exec -T afritech-api env)

REQUIRED_VARS=(
  AFRITECH_CHAIN_ENABLE_PUBLISH
  AFRITECH_CHAIN_MODE
  AFRITECH_CHAIN_RPC_URL_SEPOLIA
  AFRITECH_CHAIN_ADDRESS
  AFRITECH_CHAIN_PRIVATE_KEY
)

MISSING=0

for VAR in "${REQUIRED_VARS[@]}"; do
  if ! echo "$ENV_OUTPUT" | grep -q "^${VAR}="; then
    echo "❌ Missing env var: $VAR"
    MISSING=1
  else
    echo "✅ $VAR"
  fi
done

if [[ "$MISSING" -eq 1 ]]; then
  echo "❌ Missing required environment variables"
  exit 1
fi

# =========================
# ✅ CHECK RPC CONNECTIVITY
# =========================
echo ""
echo "==> Checking RPC connectivity"

docker compose -f "$COMPOSE_FILE" exec -T afritech-api python - <<'EOF'
from web3 import Web3
import os
import sys

rpc = os.getenv("AFRITECH_CHAIN_RPC_URL_SEPOLIA")

if not rpc:
    print("❌ RPC URL missing")
    sys.exit(1)

w3 = Web3(Web3.HTTPProvider(rpc))

if not w3.is_connected():
    print("❌ Cannot connect to Sepolia RPC")
    sys.exit(1)

print(f"✅ Connected to Sepolia (block: {w3.eth.block_number})")
EOF

# =========================
# ✅ CHECK CONTRACT CONFIG
# =========================
echo ""
echo "==> Checking contract configuration"

CONTRACT_ADDR=$(echo "$ENV_OUTPUT" | grep AFRITECH_CHAIN_CONTRACT_ADDRESS | cut -d= -f2)

if [[ -z "$CONTRACT_ADDR" ]]; then
  echo "❌ No contract address configured"
  exit 1
fi

if [[ "$CONTRACT_ADDR" == "0x123"* ]]; then
  echo "⚠️ Contract address looks like a placeholder"
else
  echo "✅ Contract address: $CONTRACT_ADDR"
fi

# =========================
# ✅ CHECK CHAIN CLIENT HEALTH
# =========================
echo ""
echo "==> Checking chain client health"

docker compose -f "$COMPOSE_FILE" exec -T afritech-api python - <<'EOF'
from afritech.chain.contracts.contract_client import chain_health

status = chain_health()
print("Chain health:", status)

if status.get("status") != "ok":
    raise SystemExit("❌ Chain client not healthy")
EOF

# =========================
# ✅ FINAL SUMMARY
# =========================
echo ""
echo "========================================="
echo " FINAL STATUS"
echo "========================================="

echo "✅ Blockchain pipeline is reachable"
echo "✅ RPC is working"
echo "✅ Contract configuration present (validate manually if needed)"
echo "✅ Chain client is operational"

echo ""
echo "⚡ READY FOR: Live smart-contract anchoring"
