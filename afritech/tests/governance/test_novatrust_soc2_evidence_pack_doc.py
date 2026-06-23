from __future__ import annotations

from pathlib import Path


DOC = Path("docs/compliance/NOVATRUST_SOC2_EVIDENCE_PACK.md")


def test_novatrust_soc2_evidence_pack_covers_public_artifacts_and_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")

    required = [
        "/trust/sandbox/demo",
        "/trust/explorer/{trust_id}/signature",
        "/trust/explorer/{trust_id}/anchor/blockchain",
        "/trust/explorer/{trust_id}/bundle.zip",
        "novatrust-verify",
        "CC6 Access Controls",
        "Processing Integrity",
        "QR-style PNG verification image",
        "not yet an external notarization system",
        "not a certification statement",
        "NovaTrustClient",
        "signatureVerified",
    ]

    for item in required:
        assert item in text
