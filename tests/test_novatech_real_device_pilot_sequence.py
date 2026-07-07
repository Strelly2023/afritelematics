from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_real_device_pilot_sequence_doc_exists() -> None:
    doc = ROOT / "docs/pilot/NOVATECH_REAL_DEVICE_PILOT_SEQUENCE_2026.md"
    assert doc.exists()
    source = doc.read_text(encoding="utf-8")

    for marker in [
        "NovaTech Real Device Pilot Sequence 2026",
        "Phase 1: NovaID",
        "Phase 2: NovaRide",
        "Phase 3: NovaPay Consumer",
        "Phase 4: NovaPay Agent",
        "rider request reaches the driver queue",
        "NovaID linkage",
        "cash-in",
        "cash out",
        "Stop Conditions",
        "Exit Criteria",
    ]:
        assert marker in source


def test_pilot_sequence_preserves_product_boundaries() -> None:
    source = (ROOT / "docs/pilot/NOVATECH_REAL_DEVICE_PILOT_SEQUENCE_2026.md").read_text(encoding="utf-8")
    assert "NovaID as the identity layer" in source
    assert "NovaRide as mobility only" in source
    assert "NovaPay as financial execution" in source
    assert "NovaTrust as evidence" in source
    assert "NovaAI advisory only" in source
