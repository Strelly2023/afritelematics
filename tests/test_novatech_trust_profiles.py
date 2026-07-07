from __future__ import annotations

from tests._ts_loader import ROOT, load_ts_exports


DOC = ROOT / "docs/architecture/NOVATECH_TRUST_PROFILE_MODEL_2026.md"


def test_trust_profile_fields_cover_identity_device_compliance_and_operations() -> None:
    identity = load_ts_exports("packages/novatech-platform-sdk/src/identity/index.ts")
    novapay = load_ts_exports("packages/novatech-platform-sdk/src/novapay/index.ts")

    identity_fields = identity["novaIdTrustProfileFields"]
    agent_fields = novapay["novapayTrustProfileFields"]

    for required in ["identityStatus", "verificationLevel", "deviceTrust", "complianceStatus", "fraudRisk", "operationalStatus"]:
        assert required in identity_fields
        assert required in agent_fields


def test_novapay_trust_profiles_require_novatrust_evidence_and_no_novaride() -> None:
    novapay = load_ts_exports("packages/novatech-platform-sdk/src/novapay/index.ts")
    consumer = novapay["novapayConsumerRequirements"]
    agent = novapay["novapayAgentRequirements"]
    compliance = novapay["novapayComplianceControls"]

    assert consumer["requiresNovaRide"] is False
    assert agent["requiresNovaRide"] is False
    assert compliance["novaRideRequired"] is False
    assert compliance["novaAIAdvisoryOnly"] is True
    assert consumer["novaTrustEvidenceRequired"]
    assert agent["novaTrustEvidenceRequired"]
    assert compliance["novaTrustEvidenceRequired"]


def test_novai_advisory_only_is_encoded_in_requirements() -> None:
    identity = load_ts_exports("packages/novatech-platform-sdk/src/identity/index.ts")
    novapay = load_ts_exports("packages/novatech-platform-sdk/src/novapay/index.ts")
    assert "advisoryOnly" not in identity["novaIdRequirements"]
    assert novapay["novapayComplianceControls"]["novaAIAdvisoryOnly"] is True


def test_trust_profile_doc_exists() -> None:
    text = DOC.read_text(encoding="utf-8")
    for marker in [
        "NovaTech Trust Profile Model 2026",
        "Required Trust Fields",
        "NovaID Trust Profile",
        "NovaPay Trust Profile",
        "Evidence Rule",
    ]:
        assert marker in text
