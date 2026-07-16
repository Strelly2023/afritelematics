#!/usr/bin/env bash
set -euo pipefail

ROOT_URL="${1:-https://novacodepro.afritechnology.com}"
API_URL="${2:-https://api.afritechnology.com}"

curl -fsS "${ROOT_URL}/novacodepro/" >/dev/null
curl -fsS "${ROOT_URL}/novacodepro/login" >/dev/null
curl -fsS "${ROOT_URL}/novacodepro/dashboard" >/dev/null
curl -fsS "${ROOT_URL}/novacodepro/solutions" >/dev/null
curl -fsS "${ROOT_URL}/novacodepro/solutions/customers" >/dev/null
curl -fsS "${API_URL}/health" >/dev/null

UNAUTH_STATUS="$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/v1/solution-engineering")"
if [[ "${UNAUTH_STATUS}" != "401" && "${UNAUTH_STATUS}" != "403" ]]; then
  echo "Expected protected solution engineering API to require auth, got ${UNAUTH_STATUS}" >&2
  exit 1
fi

INDEX_HTML="$(curl -fsS "${ROOT_URL}/novacodepro/")"
BUNDLE_PATH="$(printf '%s' "${INDEX_HTML}" | grep -oE '/novacodepro/assets/index-[^"]+\.js' | head -n 1)"
if [[ -z "${BUNDLE_PATH}" ]]; then
  echo "Unable to locate portal bundle path" >&2
  exit 1
fi

BUNDLE_JS="$(curl -fsS "${ROOT_URL}${BUNDLE_PATH}")"
if ! printf '%s' "${BUNDLE_JS}" | grep -q "Customer Solutions"; then
  echo "Portal bundle does not contain Customer Solutions" >&2
  exit 1
fi
for label in "Discovery Workspace" "Requirements Studio" "Architecture Studio" "Workflow Fabric"; do
  if ! printf '%s' "${BUNDLE_JS}" | grep -q "${label}"; then
    echo "Portal bundle does not contain ${label}" >&2
    exit 1
  fi
done

curl -fsS "${API_URL}/openapi.json" | jq -e '
  .paths
  | has("/v1/solution-engineering")
    and has("/v1/workflow-fabric")
    and has("/v1/workflows")
' >/dev/null

echo "Portal smoke checks passed."
