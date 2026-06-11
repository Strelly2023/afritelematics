from __future__ import annotations

from pathlib import Path

from afritech.guards.architecture_drift_report import validate


ROOT = Path(__file__).resolve().parents[3]
PROTOCOL_DOC = ROOT / "docs/standards/AFRICPPT_PROTOCOL_SPEC.md"
ONE_PAGER_DOC = ROOT / "docs/partners/AFRITECH_PARTNER_ARCHITECTURE_ONE_PAGER.md"
UI_SOURCE = ROOT / "dashboard/src/App.jsx"


def test_africppt_protocol_spec_is_extracted_from_unified_architecture() -> None:
    text = PROTOCOL_DOC.read_text(encoding="utf-8")

    for item in (
        "AFRICPPT PROTOCOL SPECIFICATION",
        "EXTERNAL_INTEGRATION_PROTOCOL_SURFACE",
        "docs/architecture/AFRITECH_UNIFIED_ARCHITECTURE.md",
        "external verification APIs",
        "multi-party validation",
        "Rule 1. Replay remains truth authority.",
        "Rule 3. Registry publication indexes evidence only.",
        "POST /v1/partner/verify",
        "POST /v1/trust/network/verify",
    ):
        assert item in text


def test_partner_architecture_one_pager_preserves_simplified_boundary() -> None:
    text = ONE_PAGER_DOC.read_text(encoding="utf-8")

    for item in (
        "PARTNER ARCHITECTURE ONE-PAGER",
        "SALES_AND_ONBOARDING_ARCHITECTURE_SURFACE",
        "Apps + API",
        "-> Trace",
        "-> Replay",
        "-> Evidence",
        "-> Receipt",
        "Partner Verification",
        "the dashboard explains",
        "replay proves",
    ):
        assert item in text


def test_architecture_drift_report_is_clean_and_covers_required_classes() -> None:
    report = validate()

    assert report.clean is True
    assert report.document_registry == "afritech/governance/document_registry.yaml"
    assert report.tracked_module_count >= 20
    assert report.authority_binding_verified is True
    assert report.undocumented_modules == ()
    assert report.orphan_components == ()
    assert report.undocumented_flows == ()


def test_dashboard_exposes_architecture_compliance_and_drift_surfaces() -> None:
    text = UI_SOURCE.read_text(encoding="utf-8")

    for item in (
        "Architecture Compliance Dashboard",
        "system adherence to architecture",
        "Architecture Test Status",
        "System Adherence to Architecture",
        "Drift Detection Report",
        "New modules not in architecture",
        "Orphan components",
        "Undocumented flows",
        "AfriCPPT protocol extraction",
        "Partner one-page architecture",
    ):
        assert item in text
