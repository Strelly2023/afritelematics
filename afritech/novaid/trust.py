"""NovaID trust and evidence compatibility helpers."""

from __future__ import annotations

from typing import Any

from afritech.core_platform.services import NovaTrustService


def build_identity_receipt(
    *,
    subject_id: str,
    organization_id: str,
    event_type: str,
    packet: dict[str, Any],
    trust_service: NovaTrustService | None = None,
) -> dict[str, Any]:
    service = trust_service or NovaTrustService()
    receipt = service.record(
        subject_id=subject_id,
        organization_id=organization_id,
        event_type=event_type,
        packet=packet,
    )
    return {"receipt": receipt.canonical(), "verified": service.replay(receipt)}


def verify_identity_receipt(receipt: dict[str, Any], trust_service: NovaTrustService | None = None) -> bool:
    service = trust_service or NovaTrustService()
    from afritech.core_platform.models import TrustReceipt

    return service.replay(TrustReceipt(**receipt))


__all__ = ["build_identity_receipt", "verify_identity_receipt"]
