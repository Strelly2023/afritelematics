# afriride_system/django_app/blockchain/services.py

from __future__ import annotations
from typing import Any, Dict

from afritech.chain.anchor_publisher import publish_anchor


def _normalize_anchor_result(result: Any) -> Dict[str, Any]:
    if hasattr(result, "canonical_dict"):
        value = result.canonical_dict()
        if isinstance(value, dict):
            return value

    if isinstance(result, dict):
        return result

    if hasattr(result, "__dict__"):
        return dict(result.__dict__)

    return {
        "status": "unknown",
        "raw": str(result),
    }


def _is_successful_anchor(anchor: Dict[str, Any]) -> bool:
    status = str(anchor.get("status") or "unknown")
    return status not in {"failed", "rejected", "unknown"}


def publish_proof_to_chain(proof_payload: Dict[str, Any]) -> Dict[str, Any]:
    proof_hash = str(proof_payload.get("proof_hash", "")).strip()
    mode = str(proof_payload.get("mode", "contract")).strip() or "contract"

    if not proof_hash:
        return _fallback_response(
            mode=mode,
            error="proof_hash required",
            proof_hash="",
            status="rejected",
        )

    try:
        # ✅ CORRECT: use proof_hash only (matches your publisher)
        result = publish_anchor(proof_hash)

        anchor = _normalize_anchor_result(result)

        return {
            "success": _is_successful_anchor(anchor),
            "mode": mode,
            "anchor": anchor,
        }

    except Exception as exc:
        return _fallback_response(
            mode=mode,
            error=str(exc),
            proof_hash=proof_hash,
            status="runtime_safe_fallback",
        )


def _fallback_response(
    *,
    mode: str,
    error: str,
    proof_hash: str,
    status: str,
) -> Dict[str, Any]:
    return {
        "success": False,
        "mode": "fallback",
        "requested_mode": mode,
        "error": error,
        "anchor": {
            "chain": "Public Architecture Proof Chain",
            "network": "papc-testnet",
            "method": "anchorProof",
            "status": status,
            "tx_hash": None,
            "proof_hash": proof_hash,
            "authority": "django_bridge_fallback",
        },
    }
