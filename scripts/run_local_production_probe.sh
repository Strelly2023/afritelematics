#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-https://localhost}"

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

echo "Production probe completed."
