#!/usr/bin/env bash

set -e

BASE_URL=$1

if [ -z "$BASE_URL" ]; then
  echo "Usage: ./scripts/verify_all.sh <base-url>"
  exit 1
fi

echo "========================================="
echo " AfriTech System Verification"
echo " Base URL: $BASE_URL"
echo "========================================="

# =========================
# ✅ ARCHITECTURE PROOF
# =========================
echo ""
echo "==> Checking Architecture Proof"

PROOF_RESPONSE=$(curl -s "$BASE_URL/public/architecture/proof")

echo "$PROOF_RESPONSE" | jq '.proof.runtime_boundary_status // "missing"'
echo "$PROOF_RESPONSE" | jq '.proof.proof_id // "missing"'

# =========================
# ✅ TRUST DASHBOARD
# =========================
echo ""
echo "==> Checking Trust Dashboard"

DASHBOARD_RESPONSE=$(curl -s "$BASE_URL/public/trust/dashboard")

echo "$DASHBOARD_RESPONSE" | jq '.status // "missing"'
echo "$DASHBOARD_RESPONSE" | jq '.integrity.runtime_boundary_status // "missing"'

# =========================
# ✅ DEMO READINESS
# =========================
echo ""
echo "==> Checking Demo"

DEMO_RESPONSE=$(curl -s "$BASE_URL/public/demo/system-integrity")

echo "$DEMO_RESPONSE" | jq '.demo_readiness // "missing"'

# =========================
# ✅ CHAIN NETWORK
# =========================
echo ""
echo "==> Checking Chain Network"

echo "$DASHBOARD_RESPONSE" | jq '.chain.deterministic_receipt.network // "missing"'
echo "$DASHBOARD_RESPONSE" | jq '.chain.live_publication.network // "not_live"'

# =========================
# ✅ SUMMARY
# =========================
echo ""
echo "========================================="
echo " Summary"
echo "========================================="

RUNTIME_STATUS=$(echo "$PROOF_RESPONSE" | jq -r '.proof.runtime_boundary_status // empty')
DASHBOARD_STATUS=$(echo "$DASHBOARD_RESPONSE" | jq -r '.status // empty')
DEMO_STATUS=$(echo "$DEMO_RESPONSE" | jq -r '.demo_readiness // empty')
CHAIN_NETWORK=$(echo "$DASHBOARD_RESPONSE" | jq -r '.chain.deterministic_receipt.network // empty')

echo "Runtime:   ${RUNTIME_STATUS:-UNKNOWN}"
echo "Dashboard: ${DASHBOARD_STATUS:-UNKNOWN}"
echo "Demo:      ${DEMO_STATUS:-UNKNOWN}"
echo "Chain:     ${CHAIN_NETWORK:-UNKNOWN}"

# =========================
# ✅ FINAL STATUS CHECK
# =========================

if [[ "$RUNTIME_STATUS" == "VERIFIED" && "$DASHBOARD_STATUS" == "READY" && "$DEMO_STATUS" == "PARTNER_READY" ]]; then
  echo ""
  echo "✅ SYSTEM STATUS: HEALTHY"
else
  echo ""
  echo "⚠️ SYSTEM STATUS: DEGRADED"
  exit 1
fi
