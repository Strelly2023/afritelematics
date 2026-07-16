#!/usr/bin/env bash
set -euo pipefail

ROOT_URL="${1:-https://novacodepro.afritechnology.com}"
API_URL="${2:-https://api.afritechnology.com}"

curl_text() {
  curl --compressed -fsS "$1"
}

curl_text "${ROOT_URL}/novacodepro/" >/dev/null
curl_text "${ROOT_URL}/novacodepro/login" >/dev/null
curl_text "${ROOT_URL}/novacodepro/dashboard" >/dev/null
curl_text "${ROOT_URL}/novacodepro/solutions" >/dev/null
curl_text "${ROOT_URL}/novacodepro/solutions/customers" >/dev/null
curl_text "${API_URL}/health" >/dev/null

UNAUTH_STATUS="$(curl --compressed -s -o /dev/null -w "%{http_code}" "${API_URL}/v1/solution-engineering")"
if [[ "${UNAUTH_STATUS}" != "401" && "${UNAUTH_STATUS}" != "403" ]]; then
  echo "Expected protected solution engineering API to require auth, got ${UNAUTH_STATUS}" >&2
  exit 1
fi

INDEX_HTML="$(curl_text "${ROOT_URL}/novacodepro/")"
ASSET_PATHS="$(
  printf '%s' "${INDEX_HTML}" \
    | grep -oE '/novacodepro/assets/[^"]+\.js' \
    | sort -u
)"
if [[ -z "${ASSET_PATHS}" ]]; then
  echo "Unable to locate portal bundle path" >&2
  exit 1
fi

ASSET_BUNDLE="$(
  while IFS= read -r asset; do
    [[ -z "${asset}" ]] && continue
    curl_text "${ROOT_URL}${asset}"
  done <<< "${ASSET_PATHS}"
)"
for label in "Customer Solutions" "Discovery Workspace" "Requirements Studio" "Architecture Studio" "Workflow Fabric"; do
  if ! printf '%s' "${ASSET_BUNDLE}" | grep -q "${label}"; then
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
