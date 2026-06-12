# afritech/chain/anchor_publisher.py

from typing import Dict, Any

from afritech.chain.types import ChainReceipt

# ✅ Primary (ELITE+) → smart contract anchoring
from afritech.chain.contracts.contract_client import anchor_proof_on_chain

# ✅ Optional fallback (legacy raw tx mode)
from afritech.chain.sepolia_client import send_proof_hash


# =========================
# ✅ CONSTANTS
# =========================

SEPOLIA_EXPLORER_BASE = "https://sepolia.etherscan.io/tx/"


# =========================
# ✅ CORE PUBLISH FUNCTION
# =========================

def publish_anchor(
    proof_hash: str,
    *,
    profile_name: str | None = None,
    require_live: bool = False,
) -> ChainReceipt:
    """
    Publishes a proof hash using Smart Contract (primary)
    with fallback to raw transaction and finally deterministic fallback unless
    require_live is true.

    Priority:
    1. Smart contract (ELITE+)
    2. Raw transaction fallback
    3. Runtime-safe fallback

    This ensures:
    - ✅ Maximum reliability
    - ✅ No system crashes
    - ✅ Always returns a ChainReceipt
    """

    anchor_id = f"arch-{proof_hash[:12]}"

    # =========================
    # ✅ 1. SMART CONTRACT (PRIMARY)
    # =========================
    try:
        result: Dict[str, Any] = anchor_proof_on_chain(
            anchor_id=anchor_id,
            proof_hash=proof_hash,
            profile_name=profile_name,
        )

        if result.get("status") == "live":
            tx_hash = result["tx_hash"]

            return ChainReceipt(
                tx_hash=tx_hash,
                block_number=result.get("block_number"),
                network=str(result.get("network", "sepolia")),
                explorer_url=str(result.get("explorer_url") or f"{SEPOLIA_EXPLORER_BASE}{tx_hash.removeprefix('0x')}"),
                status="live",
                chain_id=int(result.get("chain_id", 11155111)),
                chain_name=str(result.get("chain_name", "Ethereum Sepolia")),
                proof_hash=proof_hash,
                authority="smart_contract",
                contract_address=result.get("contract_address"),
                method="anchorProof",
                source="anchor_publisher.contract",
                meta={
                    "event": result.get("event"),
                },
            )
        contract_failure_reason = str(result.get("error") or result.get("status") or "contract_publish_not_live")

    except Exception as contract_error:
        contract_failure_reason = str(contract_error)

    if require_live:
        raise RuntimeError(f"Smart contract publication failed: {contract_failure_reason}")

    # =========================
    # ✅ 2. RAW TX FALLBACK
    # =========================
    try:
        receipt = send_proof_hash(proof_hash)

        tx_hash = receipt["tx_hash"]

        return ChainReceipt(
            tx_hash=tx_hash,
            block_number=receipt.get("block_number"),
            network="sepolia",
            explorer_url=f"{SEPOLIA_EXPLORER_BASE}{tx_hash}",
            status="live",
            chain_id=11155111,
            chain_name="Ethereum Sepolia",
            proof_hash=proof_hash,
            authority="raw_transaction_fallback",
            source="anchor_publisher.legacy",
            meta={
                "gas_used": receipt.get("gas_used"),
                "note": "Used raw transaction fallback (no contract)",
            },
        )

    except Exception as raw_error:
        raw_failure_reason = str(raw_error)

    # =========================
    # ✅ 3. FINAL FALLBACK (NEVER FAIL)
    # =========================
    return ChainReceipt(
        tx_hash=f"fallback-{proof_hash[:16]}",
        block_number=None,
        network="papc-testnet",
        explorer_url=None,
        status="runtime_safe_fallback",
        chain_id=None,
        chain_name="PAPC Testnet",
        proof_hash=proof_hash,
        authority="runtime_safe_fallback",
        source="anchor_publisher.fallback",
        meta={
            "contract_failure": contract_failure_reason,
            "raw_tx_failure": raw_failure_reason,
            "note": "Live blockchain unavailable; deterministic fallback used",
        },
    )


# =========================
# ✅ OPTIONAL: DRY RUN MODE
# =========================

def simulate_anchor(proof_hash: str) -> ChainReceipt:
    """
    Deterministic simulation (no blockchain call).
    Useful for:
    - CI/CD
    - Local development
    - Unit tests

    NEVER touches chain
    """

    return ChainReceipt(
        tx_hash=f"simulated-{proof_hash[:16]}",
        block_number=0,
        network="papc-testnet",
        explorer_url=None,
        status="runtime_safe_fallback",
        chain_id=None,
        chain_name="Simulated Chain",
        proof_hash=proof_hash,
        authority="simulation",
        source="anchor_publisher.simulated",
        meta={
            "mode": "dry_run",
        },
    )
