from __future__ import annotations

from tests._ts_loader import ROOT, load_ts_exports


DOC = ROOT / "docs/architecture/NOVAPAY_AGENT_OPERATIONS_FRAMEWORK_2026.md"


def test_agent_dashboard_and_metrics_exist() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/novapay/index.ts")
    agent = exported["novapayAgentRequirements"]
    assert "Current float balance" in agent["dashboardFields"]
    assert "Commission earnings" in agent["dashboardFields"]
    assert "Transaction volume" in agent["performanceMetrics"]
    assert "Settlement accuracy" in agent["performanceMetrics"]


def test_agent_compliance_and_security_requirements_exist() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/novapay/index.ts")
    agent = exported["novapayAgentRequirements"]
    for required in [
        "MFA",
        "Device binding",
        "Transaction PIN",
        "Audit logging",
        "Fraud detection",
        "Role-based permissions",
        "KYC",
        "KYB",
        "AML",
        "CTF",
        "Suspicious transaction reporting",
        "Record retention",
    ]:
        joined = " ".join(agent["securityRequirements"] + agent["complianceRequirements"])
        assert required in joined


def test_agent_novatrust_evidence_is_required() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/novapay/index.ts")
    agent = exported["novapayAgentRequirements"]
    evidence = agent["novaTrustEvidenceRequired"]
    for required in [
        "Identity Verified",
        "Business Verified",
        "Cash Received",
        "Ledger Entry",
        "Settlement Record",
        "Digital Signature",
        "Replay Evidence",
        "Audit Package",
    ]:
        assert required in evidence


def test_agent_operations_docs_exist() -> None:
    text = DOC.read_text(encoding="utf-8")
    for marker in [
        "NovaPay Agent Operations Framework 2026",
        "Operating Model",
        "Cash Management",
        "Security Controls",
        "Compliance Controls",
        "Evidence Requirements",
    ]:
        assert marker in text
