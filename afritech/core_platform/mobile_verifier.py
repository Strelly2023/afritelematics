"""Mobile verification helpers for scanned proof receipts."""

from __future__ import annotations

from typing import Any, Mapping

from afritech.core_platform.proof_receipts import verify_proof_receipt
from afritech.core_platform.qr_proof import decode_qr_payload


def _compute_trust_level(receipt: Mapping[str, Any], verification: Mapping[str, Any]) -> str:
    if verification.get("valid") is not True:
        return "UNTRUSTED"

    threshold = int(receipt.get("signature_threshold") or 0)
    signer_set = list(receipt.get("signer_set", []))
    if threshold and len(signer_set) >= threshold:
        return "HIGH"
    if signer_set:
        return "PARTIAL"
    return "UNKNOWN"


def verify_scanned_receipt(
    qr_data: str,
    *,
    group_public_keys: list[bytes] | None = None,
) -> dict[str, Any]:
    try:
        receipt = decode_qr_payload(qr_data)
    except ValueError as exc:
        reason = str(exc)
        return {
            "status": False,
            "reason": reason,
            "trust_level": "UNTRUSTED",
            "validators": [],
            "receipt": None,
            "verification": {
                "valid": False,
                "reason": reason,
            },
        }
    verification = verify_proof_receipt(receipt, group_public_keys=group_public_keys)
    trust_level = _compute_trust_level(receipt, verification)
    return {
        "status": verification["valid"] is True,
        "reason": verification["reason"],
        "trust_level": trust_level,
        "validators": list(receipt.get("accepted_validators", [])),
        "receipt": receipt if verification["valid"] is True else None,
        "verification": verification,
    }


__all__ = ["verify_scanned_receipt"]
