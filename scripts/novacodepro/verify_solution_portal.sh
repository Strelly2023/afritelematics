#!/usr/bin/env bash
set -euo pipefail

ROOT_URL="${1:-https://novacodepro.afritechnology.com}"
API_URL="${2:-https://api.afritechnology.com}"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

INDEX_FILE="$TMP_DIR/index.html"
BUNDLE_FILE="$TMP_DIR/portal.js"

curl -fsS \
  -H 'Cache-Control: no-cache' \
  "${ROOT_URL}/novacodepro/?cache=$(date +%s)" \
  -o "$INDEX_FILE"

curl -fsS \
  -H 'Cache-Control: no-cache' \
  "${ROOT_URL}/novacodepro/login?cache=$(date +%s)" \
  >/dev/null
curl -fsS \
  -H 'Cache-Control: no-cache' \
  "${ROOT_URL}/novacodepro/dashboard?cache=$(date +%s)" \
  >/dev/null
curl -fsS \
  -H 'Cache-Control: no-cache' \
  "${ROOT_URL}/novacodepro/solutions?cache=$(date +%s)" \
  >/dev/null
curl -fsS \
  -H 'Cache-Control: no-cache' \
  "${ROOT_URL}/novacodepro/solutions/customers?cache=$(date +%s)" \
  >/dev/null
curl -fsS "${API_URL}/health" >/dev/null

UNAUTH_STATUS="$(curl --compressed -s -o /dev/null -w "%{http_code}" "${API_URL}/v1/solution-engineering")"
if [[ "${UNAUTH_STATUS}" != "401" && "${UNAUTH_STATUS}" != "403" ]]; then
  echo "Expected protected solution engineering API to require auth, got ${UNAUTH_STATUS}" >&2
  exit 1
fi

BUNDLE_PATH="$(
  grep -oE '/novacodepro/assets/index-[^"]+\.js' "$INDEX_FILE" |
    head -n 1
)"

if [[ -z "${BUNDLE_PATH}" ]]; then
  echo "Unable to locate portal bundle path" >&2
  exit 1
fi

curl -fsS \
  -H 'Cache-Control: no-cache' \
  "${ROOT_URL}${BUNDLE_PATH}?cache=$(date +%s)" \
  -o "$BUNDLE_FILE"

for label in "Customer Solutions" "Discovery Workspace" "Requirements Studio" "Architecture Studio" "Workflow Fabric"; do
  if ! grep -aFq -- "${label}" "$BUNDLE_FILE"; then
    echo "Portal bundle does not contain ${label}" >&2
    exit 1
  fi
done

curl_text "${API_URL}/openapi.json" | jq -e '
  .paths
  | has("/v1/solution-engineering")
    and has("/v1/workflow-fabric")
    and has("/v1/workflows")
' >/dev/null

echo "Portal smoke checks passed."
