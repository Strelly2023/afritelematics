from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ARCH = ROOT / "docs/architecture/AFRIRIDE_TRUST_NETWORK_ARCHITECTURE.md"
PORTAL = ROOT / "docs/portal/AFRIRIDE_DEVELOPER_PORTAL_AND_DOCS.md"
DECK = ROOT / "docs/pitch/AFRIRIDE_TRUST_NETWORK_PARTNER_INVESTOR_DECK.md"
STRATEGY = ROOT / "docs/strategy/AFRIRIDE_REAL_MARKET_LAUNCH_STRATEGY.md"


def test_trust_network_architecture_covers_launch_enterprise_and_research() -> None:
    text = ARCH.read_text(encoding="utf-8")
    for item in (
        "AFRIRIDE TRUST NETWORK ARCHITECTURE",
        "onboard partners",
        "publish trust registry",
        "position as infrastructure",
        "government / enterprise pilots",
        "build trust APIs",
        "create verification network",
        "POST /v1/trust/network/verify",
    ):
        assert item in text


def test_developer_portal_doc_covers_registry_and_network_docs() -> None:
    text = PORTAL.read_text(encoding="utf-8")
    for item in (
        "AFRIRIDE DEVELOPER PORTAL AND DOCS",
        "trust API reference",
        "SDK downloads",
        "trust registry guide",
        "verification network guide",
        "publish trust registry entry",
    ):
        assert item in text


def test_pitch_deck_and_market_strategy_preserve_bounded_claims() -> None:
    deck = DECK.read_text(encoding="utf-8")
    strategy = STRATEGY.read_text(encoding="utf-8")

    for item in (
        "TRUST NETWORK PARTNER AND INVESTOR DECK",
        "trust infrastructure for mobility",
        "partner verification substrate",
        "raise and partnership ask",
    ):
        assert item in deck

    for item in (
        "REAL MARKET LAUNCH STRATEGY",
        "Phase A. Platform Launch",
        "Phase B. Enterprise Penetration",
        "Phase C. Research Differentiation",
        "Go to market on infrastructure trust",
        "global verification network rollout",
    ):
        assert item in strategy
