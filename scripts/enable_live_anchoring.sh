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
import os
import re
import sys

from afritech.chain.contracts.deployment_config import get_deployment_profile
from afritech.chain.types import ChainReceipt
from afritech.ecosystem_evolution import (
    build_ecosystem_evolution_certificate,
    build_global_verification_bundle,
    publish_live_ecosystem_anchor,
    record_live_ecosystem_anchor,
    verify_ecosystem_evolution_certificate,
)

profile = sys.argv[1]


def _recover_pending_receipt(error: Exception) -> ChainReceipt:
    message = str(error)
    match = re.search(r"HexBytes\('(?P<hex>0x[a-fA-F0-9]{64})'\)", message) or re.search(
        r"(?P<hex>0x[a-fA-F0-9]{64})",
        message,
    )
    if not match:
        raise error

    tx_hash = match.group("hex")
    chain_profile = get_deployment_profile(profile)
    timeout = int(os.getenv("AFRITECH_CHAIN_PENDING_TX_TIMEOUT", "600"))

    from web3 import Web3

    web3 = Web3(Web3.HTTPProvider(str(chain_profile["rpc_url"])))
    if not web3.is_connected():
        raise RuntimeError(f"cannot recover pending transaction {tx_hash}: Web3 not connected") from error

    try:
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
    except Exception as wait_error:
        raise RuntimeError(
            f"submitted transaction {tx_hash} was not mined within recovery timeout {timeout}s"
        ) from wait_error

    transaction_status = int(tx_receipt.get("status", 0))
    if transaction_status != 1:
        raise RuntimeError(f"submitted transaction {tx_hash} was mined but reverted")

    proof_hash = str(build_global_verification_bundle().canonical_dict()["global_bundle_hash"])
    return ChainReceipt(
        tx_hash=tx_hash,
        block_number=int(tx_receipt["blockNumber"]),
        network=str(chain_profile["network"]),
        explorer_url=f"{chain_profile['explorer_base_url']}{tx_hash.removeprefix('0x')}",
        status="live",
        chain_id=int(chain_profile["chain_id"]),
        chain_name=str(chain_profile["chain_name"]),
        contract_address=str(chain_profile["contract_address"]),
        method="anchorProof",
        proof_hash=proof_hash,
        authority="smart_contract",
        source="anchor_publisher.contract.recovered",
        meta={
            "recovered_after_initial_timeout": True,
            "original_error": message,
            "recovery_timeout_seconds": timeout,
            "transaction_status": transaction_status,
        },
    )


try:
    receipt = publish_live_ecosystem_anchor(profile_name=profile, require_live=True)
except RuntimeError as exc:
    receipt = _recover_pending_receipt(exc)

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
