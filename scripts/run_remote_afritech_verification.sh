#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-}"
if [ -z "$BASE_URL" ]; then
  echo "usage: ./scripts/run_remote_afritech_verification.sh <base-url> [anchor-id]" >&2
  exit 1
fi

ANCHOR_ID="${2:-}"

echo "Remote verification target: $BASE_URL"
echo

health() {
  echo "==> health"
  curl -fsS "$BASE_URL/" | python3 -m json.tool
  echo
}

token() {
  curl -fsS -X POST "$BASE_URL/v1/auth/token" \
    -H "Content-Type: application/json" \
    -d '{"user_id":"staging-operator","role":"OPERATOR"}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["token"])'
}

read_authed() {
  local path="$1"
  local bearer="$2"
  echo "==> $path"
  curl -fsS "$BASE_URL$path" -H "Authorization: Bearer $bearer" | python3 -m json.tool
  echo
}

health
OPERATOR_TOKEN="$(token)"

read_authed "/v1/ops/observability/dashboard" "$OPERATOR_TOKEN"
read_authed "/v1/ops/audit/dashboard" "$OPERATOR_TOKEN"
read_authed "/v1/partners/registry" "$OPERATOR_TOKEN"
read_authed "/v1/trust/registry" "$OPERATOR_TOKEN"

echo "==> public verification health"
curl -fsS "$BASE_URL/public/verify/health" | python3 -m json.tool
echo

echo "==> public registry"
curl -fsS "$BASE_URL/public/registry" | python3 -m json.tool
echo

if [ -n "$ANCHOR_ID" ]; then
  echo "==> public verify $ANCHOR_ID"
  curl -fsS "$BASE_URL/public/verify/$ANCHOR_ID" | python3 -m json.tool
  echo
fi

echo "Remote verification completed."
