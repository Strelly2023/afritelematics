from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SIM = ROOT / "docs/pitch/AFRITECH_LIVE_PARTNER_SIMULATION.md"
CLOSE = ROOT / "docs/pitch/AFRITECH_FINAL_5_MINUTE_CLOSING_SCRIPT.md"
NEGOTIATION = ROOT / "docs/business/AFRITECH_NEGOTIATION_SCENARIOS.md"
CONTRACT = ROOT / "docs/business/AFRITECH_FIRST_CONTRACT_TEMPLATE.md"


def test_live_partner_simulation_anchors_to_runtime_surfaces() -> None:
    text = SIM.read_text(encoding="utf-8")
    for item in (
        "LIVE PARTNER SIMULATION",
        "We already have logs. Why do we need this?",
        "Why should we trust your verification endpoint?",
        "POST /system/external-verify/{ride_id}",
        "GET /system/trust-sla",
        "WS /ws/system/trust",
        "one proof artifact",
    ):
        assert item in text


def test_final_closing_script_ends_on_pilot_scope_review() -> None:
    text = CLOSE.read_text(encoding="utf-8")
    for item in (
        "FINAL 5-MINUTE CLOSING SCRIPT",
        "replay, the signed receipt, the external verification",
        "one bounded pilot",
        "pilot scope review this week",
    ):
        assert item in text


def test_negotiation_scenarios_protect_runtime_boundaries() -> None:
    text = NEGOTIATION.read_text(encoding="utf-8")
    for item in (
        "NEGOTIATION SCENARIOS",
        "Price Pressure",
        "Procurement Delay",
        "Questions SLA Language",
        "signed receipt integrity",
        "trust SLA clarity",
    ):
        assert item in text


def test_first_contract_template_references_real_runtime_surfaces() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    for item in (
        "FIRST CONTRACT TEMPLATE",
        "bounded verification pilot",
        "USD 18,000",
        "GET /ride/{ride_id}/replay",
        "POST /system/external-verify/{ride_id}",
        "GET /system/trust-sla",
        "WS /ws/system/trust",
        "Replay-backed evidence remains the authority",
    ):
        assert item in text
