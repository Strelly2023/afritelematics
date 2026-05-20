from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/pitch/AfriRide_Investor_Pitch_Deck.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: INVESTOR POSITIONING",
    "CLASSIFICATION: ISOLATED INVESTOR COMMUNICATION SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

CURRENT_STATUS_ITEMS = (
    "constitutional runtime integration",
    "replay-safe execution engine",
    "governance enforcement validators",
    "continuity scenario simulations",
    "proof-bound system validation",
    "bounded AfriRide continuity proof behavior",
)

PLANNED_OR_EXPLORATORY_ITEMS = (
    "scheduled rides",
    "multi-destination routing",
    "guest booking",
    "fare splitting",
    "pricing transparency",
    "ride comparison",
    "live trip sharing",
    "ride anomaly detection",
    "identity verification",
    "AfriRide One membership layer",
    "logistics and service integrations",
)

RISK_TRANSPARENCY_ITEMS = (
    "global scale operations",
    "mass user adoption",
    "fully deployed ride marketplace",
    "creator-independent operability",
)

FORBIDDEN_CLAIMS = (
    "currently deployed global ride marketplace",
    "active revenue claims",
    "global deployment readiness achieved",
    "mass user adoption proven",
    "fully deployed ride marketplace proven",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start)
    return text[start:end]


def test_investor_pitch_has_isolated_positioning_status() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "Documentation and investor communication must preserve or isolate all claims." in text
    assert "does not define proof truth" in text
    assert "does not claim global deployment readiness" in text


def test_investor_pitch_separates_current_status_from_product_vision() -> None:
    text = read_doc()
    current = section(text, "## 6. Current System Status", "## 7. Product Vision")
    vision = section(text, "## 7. Product Vision", "## 8. Why This Matters")

    assert "Status: [Implemented / In Development]" in current
    for item in CURRENT_STATUS_ITEMS:
        assert item in current

    assert "consumer ride marketplace features are not yet deployed" in current
    assert "Status: [Planned / Exploratory]" in vision
    for item in PLANNED_OR_EXPLORATORY_ITEMS:
        assert item in vision
        assert item not in current


def test_investor_pitch_contains_risk_transparency() -> None:
    text = read_doc()
    risks = section(text, "## 14. Risk Transparency", "## 15. Roadmap")

    assert "Not yet proven:" in risks
    for item in RISK_TRANSPARENCY_ITEMS:
        assert item in risks

    assert "current claims" in risks


def test_investor_pitch_has_preserve_or_isolate_boundary() -> None:
    text = read_doc()

    assert "operations may optimize reproducibility" in text
    assert "but may not redefine admissibility" in text
    assert "isolated investor communication surface" in text
    assert "does not modify `afritech.demo.proof`" in text
    assert "does not expand proof scope beyond the bounded AfriRide domain" in text


def test_investor_pitch_does_not_inflate_claims() -> None:
    text = read_doc().lower()

    for claim in FORBIDDEN_CLAIMS:
        assert claim not in text

    assert "not live monetization assertions" in text
    assert "not claimed" in text
    assert "not current proof claims" in text
