from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEAL = ROOT / "docs/partners/AFRIRIDE_FIRST_PARTNER_DEAL_STRATEGY.md"
PACKAGING = ROOT / "docs/business/AFRIRIDE_PRICING_AND_PACKAGING_REFINEMENT.md"
LAUNCH = ROOT / "docs/portal/AFRIRIDE_TRUST_EXPLORER_PUBLIC_LAUNCH.md"
OUTREACH = ROOT / "docs/standards/AFRIRIDE_PROTOCOL_STANDARDIZATION_AND_OUTREACH.md"


def test_first_partner_deal_strategy_is_step_by_step() -> None:
    text = DEAL.read_text(encoding="utf-8")

    for item in (
        "FIRST PARTNER DEAL STRATEGY",
        "Step-By-Step Deal Path",
        "Step 3. Run a sandbox verification session",
        "Step 5. Propose a bounded pilot",
        "sandbox verification",
        "one verified packet",
        "first annual agreement negotiation started",
    ):
        assert item in text


def test_pricing_and_packaging_refinement_covers_real_market_packages() -> None:
    text = PACKAGING.read_text(encoding="utf-8")

    for item in (
        "PRICING AND PACKAGING REFINEMENT",
        "Explorer Launch Package",
        "Verification Workflow Package",
        "Audit And Compliance Package",
        "Network Participation Package",
        "monthly platform fee plus packet volume allowance",
        "price entry low enough for sandbox adoption",
    ):
        assert item in text


def test_trust_explorer_public_launch_doc_covers_public_panels_and_boundaries() -> None:
    text = LAUNCH.read_text(encoding="utf-8")

    for item in (
        "TRUST EXPLORER PUBLIC LAUNCH",
        "Curated Evidence Launch",
        "Partner Demo Launch",
        "Public Protocol Positioning",
        "Trust Explorer Registry",
        "Verification Visualization",
        "not a second truth layer",
    ):
        assert item in text


def test_protocol_standardization_and_outreach_covers_positioning_and_workshops() -> None:
    text = OUTREACH.read_text(encoding="utf-8")

    for item in (
        "PROTOCOL STANDARDIZATION AND OUTREACH",
        "Protocol Ecosystem",
        "External Systems Registering On The Protocol",
        "External Systems Depending On The Protocol",
        "Standardization Goal",
        "Protocol Adoption Path",
        "Smart Contract Surfaces",
        "Outreach Targets",
        "Outreach Sequence",
        "technical workshop",
        "smart contracts are bounded settlement and anchoring surfaces",
        "reference implementation",
        "replay-linked verification standard",
    ):
        assert item in text
