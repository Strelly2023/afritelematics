from __future__ import annotations

from pathlib import Path

from tests._ts_loader import ROOT, load_ts_exports


DOC = ROOT / "docs/architecture/NOVAID_IDENTITY_FRAMEWORK_2026.md"


def test_novaid_identity_types_exist() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/identity/index.ts")
    identity_types = exported["novaIdIdentityTypes"]
    keys = [item["key"] for item in identity_types]
    assert keys == ["personal", "business", "employee", "partner", "inspector"]
    for item in identity_types:
        for field in [
            "purpose",
            "eligibility",
            "requiredInformation",
            "verificationRequirements",
            "securityRequirements",
            "allowedRoles",
            "trustAttributes",
            "verificationLevel",
        ]:
            assert field in item
        assert item["eligibility"]
        assert item["requiredInformation"]
        assert item["verificationRequirements"]
        assert item["securityRequirements"]
        assert item["trustAttributes"]


def test_novaid_verification_levels_are_complete() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/identity/index.ts")
    levels = exported["novaIdVerificationLevels"]
    assert [item["level"] for item in levels] == list(range(7))
    assert levels[-1]["description"].startswith("Fully trusted identity")


def test_novaid_trust_profile_fields_are_present() -> None:
    exported = load_ts_exports("packages/novatech-platform-sdk/src/identity/index.ts")
    fields = exported["novaIdTrustProfileFields"]
    for required in [
        "identityStatus",
        "verificationLevel",
        "emailVerified",
        "phoneVerified",
        "deviceTrust",
        "biometricVerified",
        "organizationVerified",
        "roleVerified",
        "complianceStatus",
        "lastSecurityReview",
        "riskScore",
        "fraudRisk",
        "operationalStatus",
    ]:
        assert required in fields


def test_novaid_docs_exist() -> None:
    text = DOC.read_text(encoding="utf-8")
    for marker in [
        "NovaID Identity Framework 2026",
        "NovaID authenticates and verifies identity",
        "Verification Levels",
        "Trust Attributes",
        "NovaAI only for advisory guidance",
    ]:
        assert marker in text
