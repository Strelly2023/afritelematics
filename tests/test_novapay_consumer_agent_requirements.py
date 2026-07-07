from __future__ import annotations

from tests._ts_loader import ROOT, load_ts_exports


DOC = ROOT / "docs/architecture/NOVAPAY_CONSUMER_AGENT_REQUIREMENTS_2026.md"


def test_novapay_consumer_requirements_exist() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/novapay/index.ts")
    consumer = exported["novapayConsumerRequirements"]
    for field in [
        "eligibility",
        "personalInformation",
        "basicKyc",
        "standardKyc",
        "enhancedKyc",
        "securityRequirements",
        "walletSetup",
        "consumerServices",
        "complianceRules",
        "consumerTrustProfile",
        "requiresNovaRide",
        "requiresNovaAI",
        "advisoryOnly",
        "novaTrustEvidenceRequired",
    ]:
        assert field in consumer
    assert consumer["requiresNovaRide"] is False
    assert consumer["requiresNovaAI"] is False
    assert consumer["advisoryOnly"] is True
    assert "international remittance" in " ".join(consumer["consumerServices"]).lower()


def test_novapay_agent_requirements_exist() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/novapay/index.ts")
    agent = exported["novapayAgentRequirements"]
    for field in [
        "eligibility",
        "registration",
        "kyb",
        "personalVerification",
        "financialRequirements",
        "agentEquipment",
        "operationalServices",
        "cashManagement",
        "securityRequirements",
        "complianceRequirements",
        "dashboardFields",
        "performanceMetrics",
        "agentTrustProfile",
        "requiresNovaRide",
        "advisoryOnly",
        "novaTrustEvidenceRequired",
    ]:
        assert field in agent
    assert agent["requiresNovaRide"] is False
    assert agent["advisoryOnly"] is True
    assert "customer support" in " ".join(agent["operationalServices"]).lower()


def test_novapay_verification_levels_are_complete() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/novapay/index.ts")
    consumer_levels = exported["novapayConsumerVerificationLevels"]
    agent_levels = exported["novapayAgentVerificationLevels"]
    assert [item["level"] for item in consumer_levels] == list(range(5))
    assert [item["level"] for item in agent_levels] == list(range(5))


def test_novapay_docs_exist() -> None:
    text = DOC.read_text(encoding="utf-8")
    for marker in [
        "NovaPay Consumer and Agent Requirements 2026",
        "Consumer Requirements",
        "Agent Requirements",
        "NovaPay Consumer does not require NovaRide",
        "NovaPay Agent does not require NovaRide",
    ]:
        assert marker in text
