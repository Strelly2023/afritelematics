# afritech/chain/receipt_decoder.py

from typing import Dict, Any, Optional

from afritech.chain.types import ChainReceipt


# =========================
# ✅ CONSTANTS
# =========================

SEPOLIA_EXPLORER_BASE = "https://sepolia.etherscan.io/tx/"


# =========================
# ✅ CORE DECODER
# =========================

def decode_chain_receipt(payload: Dict[str, Any]) -> ChainReceipt:
    """
    Normalize any chain payload into a ChainReceipt object.

    Supports:
    - ✅ Live Sepolia transactions
    - ✅ runtime_safe_fallback responses
    - ✅ partial/malformed payloads

    Never raises → always returns a safe ChainReceipt
    """

    try:
        status = payload.get("status", "unknown")

        # ✅ LIVE CHAIN RECEIPT
        if status == "live":
            tx_hash = payload.get("tx_hash", "unknown")
            network = payload.get("network", "sepolia")

            return ChainReceipt(
                tx_hash=tx_hash,
                block_number=payload.get("block_number"),
                network=network,
                explorer_url=payload.get(
                    "explorer_url",
                    f"{SEPOLIA_EXPLORER_BASE}{tx_hash}",
                ),
                status="live",
                chain_id=payload.get("chain_id", 11155111),
                chain_name=payload.get("chain_name", "Ethereum Sepolia"),
                proof_hash=payload.get("proof_hash"),
                authority=payload.get("authority", "blockchain"),
                source="receipt_decoder",
                meta={
                    "gas_used": payload.get("gas_used"),
                },
            )

        # ✅ FALLBACK MODE
        if status == "runtime_safe_fallback":
            proof_hash = payload.get("proof_hash", "unknown")

            return ChainReceipt(
                tx_hash=payload.get("tx_hash", f"fallback-{proof_hash[:16]}"),
                block_number=None,
                network=payload.get("network", "papc-testnet"),
                explorer_url=None,
                status="runtime_safe_fallback",
                chain_id=None,
                chain_name="Fallback Chain",
                proof_hash=proof_hash,
                authority="runtime_safe_fallback",
                source="receipt_decoder",
                meta={
                    "reason": payload.get("reason", "not provided"),
                },
            )

        # ✅ PENDING / UNKNOWN
        if status in ["pending", "unknown"]:
            return ChainReceipt(
                tx_hash=payload.get("tx_hash", "unknown"),
                block_number=None,
                network=payload.get("network", "unknown"),
                explorer_url=None,
                status=status,
                chain_name="Unknown",
                authority="unknown",
                source="receipt_decoder",
            )

        # ✅ FALLBACK DEFAULT (catch-all)
        return _safe_fallback(payload, reason="unrecognized status")

    except Exception as e:
        # ✅ NEVER CRASH — CRITICAL RULE
        return _safe_fallback(payload, reason=str(e))


# =========================
# ✅ SAFE FALLBACK
# =========================

def _safe_fallback(payload: Optional[Dict[str, Any]], reason: str) -> ChainReceipt:
    """
    Guaranteed-safe fallback.
    Ensures no exception escapes.
    """

    proof_hash = None
    tx_hash = "fallback-unknown"

    if isinstance(payload, dict):
        proof_hash = payload.get("proof_hash")
        tx_hash = payload.get("tx_hash", tx_hash)

    return ChainReceipt(
        tx_hash=tx_hash,
        block_number=None,
        network="unknown",
        explorer_url=None,
        status="runtime_safe_fallback",
        chain_name="Fallback Chain",
        proof_hash=proof_hash,
        authority="decoder_fallback",
        source="receipt_decoder",
        meta={
            "error": reason,
        },
    )


# =========================
# ✅ BULK DECODER (OPTIONAL)
# =========================

def decode_receipts(payloads: Optional[list]) -> list:
    """
    Decode list of receipts safely.
    Useful for:
    - future batching
    - multi-proof verification
    """

    if not payloads:
        return []

    decoded = []

    for item in payloads:
        decoded.append(decode_chain_receipt(item))

    return decoded