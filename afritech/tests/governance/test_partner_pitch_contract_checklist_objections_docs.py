from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PITCH = ROOT / "docs/pitch/AFRIRIDE_FIRST_PARTNER_PITCH_SCRIPT_AND_DECK.md"
PRICING = ROOT / "docs/business/AFRIRIDE_FIRST_CONTRACT_PRICING.md"
CHECKLIST = ROOT / "docs/portal/AFRIRIDE_TRUST_EXPLORER_GO_LIVE_CHECKLIST.md"
OBJECTIONS = ROOT / "docs/partners/AFRIRIDE_PARTNER_OBJECTION_HANDLING.md"


def test_first_partner_pitch_doc_is_meeting_ready() -> None:
    text = PITCH.read_text(encoding="utf-8")

    for item in (
        "FIRST PARTNER PITCH SCRIPT AND DECK",
        "30-Minute Meeting Flow",
        "Minute 8-14. Product Demonstration",
        "one verified packet",
        "one rejected packet diagnosis",
        "commercial offer: first contract pricing",
        "sandbox verification session",
    ):
        assert item in text


def test_first_contract_pricing_doc_contains_exact_numbers() -> None:
    text = PRICING.read_text(encoding="utf-8")

    for item in (
        "FIRST CONTRACT PRICING",
        "USD 18,000",
        "45-Day Pilot",
        "25,000",
        "USD 35 per 1,000 calls",
        "USD 72,000",
        "USD 18,000",
        "USD 6,000",
    ):
        assert item in text


def test_trust_explorer_go_live_checklist_is_execution_ready() -> None:
    text = CHECKLIST.read_text(encoding="utf-8")

    for item in (
        "TRUST EXPLORER GO-LIVE CHECKLIST",
        "Product Checklist",
        "Evidence Checklist",
        "Technical Checklist",
        "Launch Operations Checklist",
        "Go / No-Go Questions",
        "not a second truth layer",
    ):
        assert item in text


def test_partner_objection_handling_covers_real_pushback() -> None:
    text = OBJECTIONS.read_text(encoding="utf-8")

    for item in (
        "PARTNER OBJECTION HANDLING",
        "Why not just use logs?",
        "This sounds too complex for our team.",
        "Do we have to replace our existing systems?",
        "What if the Explorer or registry is wrong?",
        "Always respond with:",
        "one bounded next step",
    ):
        assert item in text
