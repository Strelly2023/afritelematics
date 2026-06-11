from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "docs/pitch/AFRITECH_LIVE_PARTNER_DEMO_FLOW.md"
SLA = ROOT / "docs/business/AFRITECH_TRUST_SLA_CONTRACT_LANGUAGE.md"
PRICING = ROOT / "docs/business/AFRITECH_VERIFICATION_GUARANTEE_PRICING.md"
OBJECTIONS = ROOT / "docs/partners/AFRITECH_RUNTIME_OBJECTION_HANDLING.md"


def test_live_partner_demo_flow_uses_real_runtime_endpoints() -> None:
    text = DEMO.read_text(encoding="utf-8")
    for item in (
        "LIVE PARTNER DEMO FLOW",
        "GET /ride/{ride_id}/replay",
        "GET /ride/{ride_id}/receipt",
        "POST /system/external-verify/{ride_id}",
        "GET /system/trust-sla",
        "WS /ws/system/trust",
        "signed proof",
        "external verification",
    ):
        assert item in text


def test_trust_sla_contract_language_preserves_authority_boundary() -> None:
    text = SLA.read_text(encoding="utf-8")
    for item in (
        "TRUST SLA CONTRACT LANGUAGE",
        "trust_score",
        "hash-chain failure count",
        "GREEN",
        "WATCH",
        "BREACH",
        "replay remains truth authority",
        "SLA explains threshold adherence only",
    ):
        assert item in text


def test_verification_guarantee_pricing_is_tied_to_runtime_surfaces() -> None:
    text = PRICING.read_text(encoding="utf-8")
    for item in (
        "VERIFICATION GUARANTEE PRICING",
        "signed receipt proof",
        "POST /system/external-verify/{ride_id}",
        "GET /system/trust-sla",
        "trust stream review support",
        "verified workflow value",
    ):
        assert item in text


def test_runtime_objection_handling_addresses_no_need_and_logs() -> None:
    text = OBJECTIONS.read_text(encoding="utf-8")
    for item in (
        'Objection 1. "We do not need this."',
        'Objection 2. "We already have logs."',
        'Objection 3. "Why should we trust your verification endpoint?"',
        'Objection 4. "What if the trust SLA goes to BREACH?"',
        "one runtime endpoint",
        "verifiable operational truth",
    ):
        assert item in text
