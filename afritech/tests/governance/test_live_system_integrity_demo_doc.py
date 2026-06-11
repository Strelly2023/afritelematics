from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/partners/AFRITECH_LIVE_SYSTEM_INTEGRITY_DEMO.md"


def test_live_system_integrity_demo_doc_covers_public_proof_and_dashboard() -> None:
    text = DOC.read_text(encoding="utf-8")

    for required in (
        "PARTNER LIVE SYSTEM INTEGRITY DEMO",
        "/public/architecture/health",
        "/public/architecture/proof",
        "/public/verify/{anchor_id}",
        "/public/demo/system-integrity",
        "/v1/system/integrity/dashboard",
        "The anchor proves export integrity only.",
        "Replay and governed execution remain the authority.",
    ):
        assert required in text
