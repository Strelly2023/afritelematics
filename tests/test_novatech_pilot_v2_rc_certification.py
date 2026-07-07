from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pilot_v2_rc_certification_doc_exists() -> None:
    doc = ROOT / "docs/pilot/NOVATECH_PILOT_V2_RC_CERTIFICATION_2026.md"
    assert doc.exists()
    source = doc.read_text(encoding="utf-8")

    for marker in [
        "NovaTech Pilot V2 RC Certification 2026",
        "Device Qualification",
        "Identity Certification",
        "Mobility Certification",
        "Financial Certification",
        "Security Certification",
        "Performance Certification",
        "Recovery Certification",
        "Production Readiness",
        "Quantitative Acceptance Gates",
        "Failure Injection",
        "Security Validation",
        "Production Evidence Package",
        "Final Production Gate",
    ]:
        assert marker in source


def test_pilot_v2_rc_preserves_boundary_doctrine() -> None:
    source = (ROOT / "docs/pilot/NOVATECH_PILOT_V2_RC_CERTIFICATION_2026.md").read_text(encoding="utf-8")
    assert "NovaID authenticates and verifies identity." in source
    assert "NovaRide handles mobility only." in source
    assert "NovaPay executes financial services." in source
    assert "NovaTrust records evidence and audit trails." in source
    assert "NovaAI remains advisory only." in source

