"""Auditor ZIP export for NovaTrust verification artifacts."""

from __future__ import annotations

import io
import json
import zipfile
from typing import Any, Mapping

from afritech.core_platform.anchoring import anchor_packet
from afritech.core_platform.audit_export import render_audit_pdf
from afritech.core_platform.compliance_report import build_enterprise_audit_report
from afritech.core_platform.qr import render_qr_png
from afritech.core_platform.signing import sign_packet


def build_auditor_zip(
    *,
    identifier: str,
    packet: Mapping[str, Any],
    verification_url: str,
) -> bytes:
    buffer = io.BytesIO()
    signature = sign_packet(packet).canonical()
    anchor = anchor_packet(packet).canonical()
    report = build_enterprise_audit_report(packet)
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("packet.json", json.dumps(packet, indent=2, sort_keys=True, default=str))
        archive.writestr("signature.json", json.dumps(signature, indent=2, sort_keys=True))
        archive.writestr("anchor.json", json.dumps(anchor, indent=2, sort_keys=True))
        archive.writestr("compliance-report.json", json.dumps(report, indent=2, sort_keys=True, default=str))
        archive.writestr("audit.pdf", render_audit_pdf(packet, verification_url=verification_url))
        archive.writestr("verification-qr.png", render_qr_png(verification_url))
        archive.writestr(
            "README.txt",
            "\n".join(
                [
                    "NovaTrust auditor export bundle",
                    f"Identifier: {identifier}",
                    f"Explorer: {verification_url}",
                    "Verify packet.json against signature.json.",
                    "Use anchor.json for chain-of-trust metadata.",
                ]
            ),
        )
    return buffer.getvalue()
