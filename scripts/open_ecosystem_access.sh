#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-}"
if [[ -z "$BASE_URL" ]]; then
  echo "usage: ./scripts/open_ecosystem_access.sh https://<trust-node-domain>" >&2
  exit 1
fi

BASE_URL="${BASE_URL%/}"

ENDPOINTS=(
  "/health"
  "/public/feature-registry"
  "/public/feature-registry/verify"
  "/public/trust-infrastructure"
  "/public/trust-infrastructure/verify"
  "/public/global-verification"
  "/public/global-verification/verify"
  "/public/ecosystem-evolution"
  "/public/ecosystem-evolution/verify"
  "/public/ecosystem-evolution/standard"
  "/public/ecosystem-evolution/portal"
)

echo "Opening ecosystem verification access for $BASE_URL"
for endpoint in "${ENDPOINTS[@]}"; do
  echo "==> $endpoint"
  curl -kfsS "$BASE_URL$endpoint" >/dev/null
done

echo
echo "Partner access package:"
echo "- Public portal: $BASE_URL/public/ecosystem-evolution/portal"
echo "- Feature registry: $BASE_URL/public/feature-registry"
echo "- Global verification: $BASE_URL/public/global-verification/verify"
echo "- Ecosystem verification: $BASE_URL/public/ecosystem-evolution/verify"
echo "- Verification standard: $BASE_URL/public/ecosystem-evolution/standard"
echo
echo "Ecosystem access is reachable and read-only."
