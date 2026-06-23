"""Audit export helpers for public NovaTrust packets."""

from __future__ import annotations

import textwrap
from typing import Any, Mapping

from afritech.core_platform.signing import sign_packet


def build_audit_summary(packet: Mapping[str, Any], *, verification_url: str | None = None) -> list[str]:
    identity = packet.get("identity") if isinstance(packet.get("identity"), Mapping) else {}
    decision = packet.get("decision") if isinstance(packet.get("decision"), Mapping) else {}
    payment = packet.get("payment") if isinstance(packet.get("payment"), Mapping) else {}
    trust = packet.get("trust") if isinstance(packet.get("trust"), Mapping) else {}
    explanation = packet.get("explanation") if isinstance(packet.get("explanation"), Mapping) else {}
    signature = sign_packet(packet)
    return [
        "NovaTech Core Platform Audit Export",
        f"Actor: {identity.get('identity_id', 'unknown')}",
        f"Organization: {identity.get('organization_id', trust.get('organization_id', 'unknown'))}",
        f"Decision: {decision.get('decision', 'unknown')} - {decision.get('reason', 'unknown')}",
        f"Payment: {payment.get('status', 'unknown')} via {payment.get('provider', 'unknown')}",
        f"Receipt: {payment.get('receipt_id', 'none')}",
        f"Trust ID: {trust.get('trust_id', 'unknown')}",
        f"Replay: {trust.get('replay_status', 'unknown')}",
        f"Risk: {explanation.get('risk_level', 'unknown')}",
        f"Signature scheme: {signature.scheme}",
        f"Signature: {signature.signature[:48]}...",
        f"Public key: {signature.public_key[:48]}...",
        f"Verification URL: {verification_url or 'not provided'}",
        "Execution authority: false",
    ]


def render_audit_pdf(packet: Mapping[str, Any], *, verification_url: str | None = None) -> bytes:
    """Render a compact PDF without external dependencies.

    This produces a valid single-page PDF sufficient for regulator packet
    previews. A production deployment can replace this with a branded ReportLab
    or WeasyPrint renderer without changing the API contract.
    """

    lines = []
    for line in build_audit_summary(packet, verification_url=verification_url):
        lines.extend(textwrap.wrap(str(line), width=84) or [""])
    if verification_url:
        lines.append("Embedded verification QR:")
        lines.extend(_verification_matrix(verification_url))
    text_lines = ["BT", "/F1 11 Tf", "50 780 Td"]
    for index, line in enumerate(lines[:42]):
        escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if index:
            text_lines.append("0 -16 Td")
        text_lines.append(f"({escaped}) Tj")
    text_lines.append("ET")
    stream = "\n".join(text_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    chunks = [b"%PDF-1.4\n"]
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(sum(len(chunk) for chunk in chunks))
        chunks.append(f"{idx} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
    xref_offset = sum(len(chunk) for chunk in chunks)
    chunks.append(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    chunks.append(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        chunks.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    chunks.append(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return b"".join(chunks)


def _verification_matrix(value: str) -> list[str]:
    """Return a deterministic QR-style verification matrix for PDF embedding."""

    import hashlib

    digest = hashlib.sha256(value.encode("utf-8")).digest()
    bits = "".join(f"{byte:08b}" for byte in digest)
    rows = []
    cursor = 0
    for y in range(13):
        cells = []
        for x in range(13):
            finder = (x < 3 and y < 3) or (x > 9 and y < 3) or (x < 3 and y > 9)
            if finder:
                cells.append("##")
            else:
                cells.append("##" if bits[cursor % len(bits)] == "1" else "  ")
                cursor += 1
        rows.append("".join(cells))
    return rows
