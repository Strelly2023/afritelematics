"""Stateless verification for privacy-preserving QR receipts."""

from __future__ import annotations

from typing import Any, Mapping

from afritech.core_platform.cross_chain_light_client import verify_cross_chain_bridge
from afritech.core_platform.privacy_qr import decode_privacy_qr_payload
from afritech.core_platform.zk_receipts import verify_zk_receipt


def _trust_level(
    zk_verification: Mapping[str, Any],
    bridge_verification: Mapping[str, Any] | None,
) -> str:
    if zk_verification.get("valid") is not True:
        return "UNTRUSTED"
    if bridge_verification is None:
        return "PARTIAL"
    if bridge_verification.get("valid") is True:
        return "HIGH"
    return "UNTRUSTED"


def verify_stateless_privacy_qr(
    qr_data: str,
    *,
    expected_receipt: Mapping[str, Any] | None = None,
    expected_light_client_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        payload = decode_privacy_qr_payload(qr_data)
    except ValueError as exc:
        reason = str(exc)
        return {
            "status": False,
            "reason": reason,
            "trust_level": "UNTRUSTED",
            "payload": None,
            "zk_receipt": None,
            "bridge": None,
            "verification": {
                "valid": False,
                "reason": reason,
            },
        }

    zk_receipt = payload.get("zk_receipt")
    if not isinstance(zk_receipt, Mapping):
        return {
            "status": False,
            "reason": "qr_missing_zk_receipt",
            "trust_level": "UNTRUSTED",
            "payload": payload,
            "zk_receipt": None,
            "bridge": payload.get("bridge"),
            "verification": {
                "valid": False,
                "reason": "qr_missing_zk_receipt",
            },
        }

    zk_verification = verify_zk_receipt(zk_receipt, expected_receipt=expected_receipt)
    bridge = payload.get("bridge")
    bridge_verification: dict[str, Any] | None = None
    if bridge is not None:
        if not isinstance(bridge, Mapping):
            bridge_verification = {"valid": False, "reason": "qr_invalid_bridge"}
        else:
            bridge_verification = verify_cross_chain_bridge(
                bridge,
                expected_commitment=str(zk_verification.get("commitment", "")).strip()
                or None,
                expected_light_client_state=expected_light_client_state,
            )

    valid = zk_verification.get("valid") is True and (
        bridge_verification is None or bridge_verification.get("valid") is True
    )
    trust_level = _trust_level(zk_verification, bridge_verification)
    reason = (
        bridge_verification.get("reason")
        if bridge_verification is not None and bridge_verification.get("valid") is False
        else zk_verification.get("reason", "stateless_verified")
    )
    if valid:
        reason = "stateless_verified"

    return {
        "status": valid,
        "reason": reason,
        "trust_level": trust_level,
        "payload": payload,
        "zk_receipt": zk_receipt,
        "bridge": bridge,
        "verification": {
            "valid": valid,
            "reason": reason,
            "zk_verification": zk_verification,
            "bridge_verification": bridge_verification,
        },
    }


__all__ = ["verify_stateless_privacy_qr"]
