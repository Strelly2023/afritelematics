#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1}"

echo "Production probe target: $BASE_URL"
echo

echo "==> health"
curl -kfsS "$BASE_URL/health" | python3 -m json.tool
echo

echo "==> public verification health"
curl -kfsS "$BASE_URL/public/verify/health" | python3 -m json.tool
echo

echo "==> public registry"
curl -kfsS "$BASE_URL/public/registry" | python3 -m json.tool
echo

echo "==> feature registry verification"
curl -kfsS "$BASE_URL/public/feature-registry/verify" | python3 -m json.tool
echo

echo "==> global verification"
curl -kfsS "$BASE_URL/public/global-verification/verify" | python3 -m json.tool
echo

echo "==> ecosystem verification"
curl -kfsS "$BASE_URL/public/ecosystem-evolution/verify" | python3 -m json.tool
echo

echo "==> interoperable verification standard"
curl -kfsS "$BASE_URL/public/ecosystem-evolution/standard" | python3 -m json.tool
echo

echo "Production probe completed."
