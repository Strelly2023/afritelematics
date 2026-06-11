from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PLAYBOOK = ROOT / "docs/partners/AFRIRIDE_PARTNER_ONBOARDING_PLAYBOOK.md"
MONETIZATION = ROOT / "docs/business/AFRIRIDE_MONETIZATION_MODEL.md"
PROTOCOL = ROOT / "docs/standards/AFRIRIDE_TRUST_PROTOCOL_SPEC.md"


def test_partner_onboarding_playbook_covers_first_five_partners() -> None:
    text = PLAYBOOK.read_text(encoding="utf-8")

    for item in (
        "PARTNER ONBOARDING PLAYBOOK",
        "First 5 Partner Targets",
        "City mobility operator",
        "Government mobility observer",
        "Marketplace infrastructure verifier",
        "first trust registry publication",
        "sandbox verification to bounded production",
    ):
        assert item in text


def test_monetization_model_covers_api_pricing_fees_and_tiers() -> None:
    text = MONETIZATION.read_text(encoding="utf-8")

    for item in (
        "AFRIRIDE MONETIZATION MODEL",
        "API pricing by verified packet volume",
        "verification fees",
        "Enterprise Tier",
        "Infrastructure Tier",
        "charge for verification workflows",
    ):
        assert item in text


def test_protocol_spec_positions_afriride_as_verification_standard() -> None:
    text = PROTOCOL.read_text(encoding="utf-8")

    for item in (
        "AFRIRIDE TRUST PROTOCOL SPECIFICATION",
        "replay-linked verification standard",
        "trust registry entry",
        "witness quorum record",
        "Registry Publication Flow",
        "mobility trust packet standard",
        "formal standards body approval",
    ):
        assert item in text
