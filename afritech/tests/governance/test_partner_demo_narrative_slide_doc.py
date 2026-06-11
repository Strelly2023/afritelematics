from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/pitch/AFRITECH_PARTNER_DEMO_NARRATIVE_SLIDE.md"


def test_partner_demo_narrative_slide_covers_external_proof_story() -> None:
    text = DOC.read_text(encoding="utf-8")

    for required in (
        "PARTNER DEMO NARRATIVE SLIDE",
        "AfriTech: A system that proves its own integrity",
        "ADR -> RULE -> BIND -> GUARD -> CI",
        "/public/architecture/proof",
        "/public/architecture/chain/{anchor_id}",
        "/public/verify/{anchor_id}",
        "The anchor proves publication and export integrity only.",
        "Replay and governed execution remain the authority.",
    ):
        assert required in text
