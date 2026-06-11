from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ONBOARDING_DOC = ROOT / "docs/partners/AFRIRIDE_PARTNER_ONBOARDING_KIT.md"
COMPLIANCE_DOC = ROOT / "docs/compliance/AFRIRIDE_ENTERPRISE_HARDENING_ALIGNMENT.md"
CRYPTO_DOC = ROOT / "docs/cryptography/AFRIRIDE_ADVANCED_CRYPTOGRAPHY_EXTENSION.md"


def test_partner_onboarding_kit_covers_sdk_distribution_and_tutorials() -> None:
    text = ONBOARDING_DOC.read_text(encoding="utf-8")

    for item in (
        "PARTNER ONBOARDING KIT",
        "SDK Distribution",
        "verification tutorial",
        "GET /v1/partner/anchors/{anchor_id}",
        "sandbox-first installation guidance",
        "tutorial 3: mismatch diagnosis and rejection handling",
        "partners can onboard to a replay-backed verification protocol",
    ):
        assert item in text


def test_enterprise_hardening_doc_covers_compliance_audit_and_legal_formats() -> None:
    text = COMPLIANCE_DOC.read_text(encoding="utf-8")

    for item in (
        "ENTERPRISE HARDENING ALIGNMENT",
        "ISO-style control ownership",
        "SOC2-style change evidence",
        "enterprise audit bundle export",
        "REGULATORY_AUDIT_V1",
        "AFFIDAVIT_SUPPORT_V1",
        "compliance packaging may not change truth",
    ):
        assert item in text


def test_advanced_crypto_doc_covers_merkle_batching_zk_and_multi_party_verification() -> None:
    text = CRYPTO_DOC.read_text(encoding="utf-8")

    for item in (
        "ADVANCED CRYPTOGRAPHY EXTENSION",
        "Merkle Batching For Anchors",
        "deterministic batch root",
        "Zero-Knowledge Proof Layer",
        "proof hash",
        "Multi-Party Verification",
        "quorum threshold",
        "without replacing replay authority",
    ):
        assert item in text
