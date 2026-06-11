from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "docs/pitch/AFRITECH_FIRST_PARTNER_DEMO_SCRIPT.md"
PILOT = ROOT / "docs/operations/AFRITECH_PILOT_EXECUTION_PACK.md"
EXPORT = ROOT / "docs/whitepaper/AFRITECH_ARCHITECTURE_COMPLIANCE_EXPORT_PACK.md"
REVENUE = ROOT / "docs/business/AFRITECH_FIRST_REVENUE_CONVERSION_PLAN.md"
SCRIPT = ROOT / "scripts/export_architecture_compliance_pack.sh"


def test_first_partner_demo_script_uses_dashboard_and_protocol() -> None:
    text = DEMO.read_text(encoding="utf-8")
    for item in (
        "FIRST PARTNER DEMO SCRIPT",
        "Architecture Compliance Dashboard",
        "System adherence to architecture",
        "Trust Explorer Registry",
        "AFRICPPT_PROTOCOL_SPEC.md",
        "POST /v1/partner/verify",
        "the UI explains",
        "replay proves",
    ):
        assert item in text


def test_pilot_execution_pack_is_tied_to_afrtpps() -> None:
    text = PILOT.read_text(encoding="utf-8")
    for item in (
        "AFRTPPS_BOUND_OPERATIONAL_EXECUTION_SURFACE",
        "Technology",
        "Processes",
        "People",
        "Skills",
        "architecture compliance dashboard",
        "pilot execution playbooks",
        "architecture adherence status",
    ):
        assert item in text


def test_architecture_compliance_export_pack_and_script_are_defined() -> None:
    text = EXPORT.read_text(encoding="utf-8")
    script = SCRIPT.read_text(encoding="utf-8")

    for item in (
        "ARCHITECTURE COMPLIANCE EXPORT PACK",
        "PDF packet for investor / partner review",
        "AFRICPPT_PROTOCOL_SPEC.md",
        "AFRITECH_PARTNER_ARCHITECTURE_ONE_PAGER.md",
        "drift detection status",
    ):
        assert item in text

    for item in (
        "AFRITECH_ARCHITECTURE_COMPLIANCE_EXPORT.md",
        "AFRITECH_ARCHITECTURE_COMPLIANCE_EXPORT.html",
        "python3 -m afritech.guards.architecture_drift_report",
        "AFRICPPT_PROTOCOL_SPEC.md",
        "AFRITECH_PARTNER_ARCHITECTURE_ONE_PAGER.md",
    ):
        assert item in script


def test_first_revenue_conversion_plan_connects_demo_to_paid_motion() -> None:
    text = REVENUE.read_text(encoding="utf-8")
    for item in (
        "FIRST REVENUE CONVERSION PLAN",
        "interest",
        "-> demo",
        "-> bounded pilot",
        "-> paid pilot",
        "Architecture Compliance Dashboard",
        "architecture compliance export pack",
        "pilot to paid conversion rate",
    ):
        assert item in text
