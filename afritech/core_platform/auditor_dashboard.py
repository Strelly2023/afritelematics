"""Auditor dashboard aggregation for multi-receipt verification."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from afritech.core_platform.compliance_report import build_enterprise_audit_report
from afritech.core_platform.signing import sign_packet, verify_packet_signature


def build_auditor_dashboard(
    packets: Iterable[tuple[str, Mapping[str, Any]]],
) -> dict[str, object]:
    items = []
    verified_count = 0
    for identifier, packet in packets:
        signature = sign_packet(packet)
        verified = verify_packet_signature(packet, signature)
        if verified:
            verified_count += 1
        trust = packet.get("trust") if isinstance(packet.get("trust"), Mapping) else {}
        payment = packet.get("payment") if isinstance(packet.get("payment"), Mapping) else {}
        report = build_enterprise_audit_report(packet)
        items.append(
            {
                "identifier": identifier,
                "trust_id": trust.get("trust_id", identifier),
                "receipt_id": payment.get("receipt_id"),
                "payment_status": payment.get("status"),
                "provider": payment.get("provider"),
                "signature_verified": verified,
                "control_count": len(report["controls"]),
                "explorer": f"/trust/explorer/{identifier}",
                "pdf": f"/trust/explorer/{identifier}/audit.pdf",
            }
        )
    total = len(items)
    return {
        "view": "novatrust_auditor_dashboard",
        "mode": "multi_receipt_verification",
        "total": total,
        "verified": verified_count,
        "failed": total - verified_count,
        "items": items,
        "execution_authority": False,
    }
