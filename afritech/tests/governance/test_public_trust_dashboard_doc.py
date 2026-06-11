from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/portal/AFRITECH_PUBLIC_TRUST_DASHBOARD.md"


def test_public_trust_dashboard_doc_covers_public_surfaces_and_boundaries() -> None:
    text = DOC.read_text(encoding="utf-8")
    for required in (
        "PUBLIC TRUST DASHBOARD",
        "GET /public/trust/dashboard",
        "/public/architecture/proof",
        "/public/architecture/chain/{anchor_id}",
        "/public/verify/{anchor_id}",
        "/public/demo/system-integrity",
        "replay and governed execution remain the authority",
    ):
        assert required in text
