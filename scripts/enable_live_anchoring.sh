#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-deploy/production/docker-compose.trust-node.yml}"
ENV_FILE="${ENV_FILE:-deploy/production/.env.production.trust-node}"
PROFILE="${1:-sepolia}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "missing env file: $ENV_FILE" >&2
  exit 1
fi

if grep -Eq 'replace-with|YOUR_|example\.invalid' "$ENV_FILE"; then
  echo "$ENV_FILE still contains chain placeholder values" >&2
  exit 1
fi

COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

echo "==> Checking chain readiness for $PROFILE"
COMPOSE_FILE="$COMPOSE_FILE" ENV_FILE="$ENV_FILE" ./scripts/check_chain_ready.sh

echo "==> Publishing Level 16 ecosystem anchor to $PROFILE"
"${COMPOSE[@]}" exec -T afritech-api python - "$PROFILE" <<'PY'
import json
import sys

from afritech.ecosystem_evolution import (
    build_ecosystem_evolution_certificate,
    publish_live_ecosystem_anchor,
    record_live_ecosystem_anchor,
    verify_ecosystem_evolution_certificate,
)

profile = sys.argv[1]
receipt = publish_live_ecosystem_anchor(profile_name=profile, require_live=True)
receipt_path = record_live_ecosystem_anchor(receipt)
certificate = build_ecosystem_evolution_certificate(live_receipt=receipt)
verification = verify_ecosystem_evolution_certificate(certificate)
print(json.dumps({
    "profile": profile,
    "receipt": receipt.canonical_dict(),
    "receipt_path": str(receipt_path),
    "verification": verification,
}, indent=2, sort_keys=True, default=str))
if not verification["verified"] or not verification["live_public_ledger_anchoring"]["live_receipt_verified"]:
    raise SystemExit("live anchor publication did not verify")
PY
