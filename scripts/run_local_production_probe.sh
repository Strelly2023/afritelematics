#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1}"
CURL_TLS_FLAGS=()

if [[ "${AFRITECH_PROBE_INSECURE:-0}" == "1" ]]; then
  CURL_TLS_FLAGS=(-k)
fi

echo "Production probe target: $BASE_URL"
echo

echo "==> health"
curl "${CURL_TLS_FLAGS[@]}" -fsS "$BASE_URL/health" | python3 -m json.tool
echo

echo "==> public verification health"
curl "${CURL_TLS_FLAGS[@]}" -fsS "$BASE_URL/public/verify/health" | python3 -m json.tool
echo

echo "==> public registry"
curl "${CURL_TLS_FLAGS[@]}" -fsS "$BASE_URL/public/registry" | python3 -m json.tool
echo

echo "==> feature registry verification"
curl "${CURL_TLS_FLAGS[@]}" -fsS "$BASE_URL/public/feature-registry/verify" | python3 -m json.tool
echo

echo "==> global verification"
curl "${CURL_TLS_FLAGS[@]}" -fsS "$BASE_URL/public/global-verification/verify" | python3 -m json.tool
echo

echo "==> ecosystem verification"
curl "${CURL_TLS_FLAGS[@]}" -fsS "$BASE_URL/public/ecosystem-evolution/verify" | python3 -m json.tool
echo

echo "==> interoperable verification standard"
curl "${CURL_TLS_FLAGS[@]}" -fsS "$BASE_URL/public/ecosystem-evolution/standard" | python3 -m json.tool
echo

echo "Production probe completed."
