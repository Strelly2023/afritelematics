from __future__ import annotations

from pathlib import Path


DOC = Path("docs/operations/NOVATECH_CORE_PLATFORM_PRODUCTION_OPERATION_VERIFICATION_GUIDE.md")


def test_novatech_core_platform_production_guide_covers_live_activation() -> None:
    text = DOC.read_text(encoding="utf-8")

    required = [
        "production-afritech-api",
        "production-afritech-dashboard",
        "production-nginx",
        "STRIPE_API_KEY",
        "STRIPE_LIVE_MODE=true",
        "ready_for_real_charge",
        "DATABASE_URL",
        "scripts/novatech_core_apply_migrations.py",
        "NOVATRUST_ED25519_PRIVATE_KEY_B64",
        "NOVATRUST_KMS_KEY_ID",
        "scripts/novatech_core_live_pilot.py",
        "http://16.176.215.89/trust/sandbox/demo",
        "sandbox-demo",
        "http://16.176.215.89/trust/explorer/{trust_id}",
        "/trust/explorer/{trust_id}/audit.pdf",
        "/trust/explorer/{trust_id}/signature",
        "/trust/explorer/{trust_id}/compliance-report",
        "/trust/explorer/{trust_id}/anchor",
        "/trust/explorer/{trust_id}/anchor/blockchain",
        "/trust/explorer/{trust_id}/qr.png",
        "/trust/explorer/{trust_id}/bundle.zip",
        "novatrust-verify",
        "packet.json",
        "signature.json",
        "anchor.json",
        "verification-qr.png",
        "/trust/auditor/dashboard?ids={trust_id_1},{trust_id_2}",
        "scripts/novatech_core_deploy_aws.sh",
    ]

    for item in required:
        assert item in text


def test_novatech_core_platform_production_guide_states_reality_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "Actual live payment execution and managed cloud deployment require" in normalized
    assert "explicit operator approval" in normalized
    assert "QR-style PNG verification image" in normalized
    assert "not a standards-compliant QR code" in normalized
    assert "This is NOT yet an external notarization system" in normalized
