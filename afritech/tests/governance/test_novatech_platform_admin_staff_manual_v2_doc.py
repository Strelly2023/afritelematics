from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/governance/NOVATECH_PLATFORM_ADMINISTRATOR_AND_STAFF_MANUAL_V2.md"


def test_manual_has_official_internal_document_controls() -> None:
    text = DOC.read_text(encoding="utf-8")

    for required in (
        "NOVATECH PLATFORM ADMINISTRATOR & STAFF MANUAL",
        "Version 2.0",
        "Official internal reference",
        "Document Control",
        "Authority boundary",
        "How to Use This Manual",
        "Platform Summary",
        "Operating Principles",
    ):
        assert required in text


def test_manual_covers_core_operating_layers_and_roles() -> None:
    text = DOC.read_text(encoding="utf-8")

    for required in (
        "Platform Architecture",
        "Roles and Access Model",
        "System Administrator",
        "Operations Administrator",
        "Trust Administrator",
        "Finance Administrator",
        "Developer",
        "Business Operator",
        "SaaS Administrator",
        "Security Administrator",
        "Data Steward",
        "Support Operator",
        "Organization OS",
        "Multi-Tenant SaaS Operations",
        "Controlled Execution and Safety",
        "Outcome Intelligence and Learning",
        "Federated Trust Network and Marketplace",
        "Incident Management and Escalation",
        "Change, Release, and Deployment Management",
        "Onboarding, Training, and Support",
        "Operational Cadence",
    ):
        assert required in text


def test_manual_includes_source_appendix_pack() -> None:
    text = DOC.read_text(encoding="utf-8")

    for required in (
        "Appendix Source Index",
        "Appendix A - NovaScript Governance Handbook",
        "Appendix B - AfriRide Operability Playbook",
        "Appendix H - Full-System Verification Runbook",
        "Appendix M - Phase 1 Setup Runbook",
        "Appendix S - Operational Civilization Master Plan",
        "Appendix Z - AfriCPPT Protocol Spec",
        "Appendix AA - AfriRide Trust Protocol Spec",
    ):
        assert required in text


def test_manual_is_substantial() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert len(text.split()) >= 100_000
