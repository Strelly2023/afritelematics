from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_api_contract_preflight_script_checks_driver_routes() -> None:
    source = (ROOT / "scripts/mobile/verify_novaride_api_contract.py").read_text(encoding="utf-8")
    assert "/health" in source
    assert "/live" in source
    assert "/ready" in source
    assert "/openapi.json" in source
    assert "/v1/driver/{driver_id}/availability" in source
    assert "/v1/driver/{driver_id}/ride-queue" in source
    assert '"get"' in source


def test_public_artifact_verifier_supports_apk_and_ipa() -> None:
    source = (ROOT / "scripts/mobile/verify_public_apk_release.py").read_text(encoding="utf-8")
    assert "application/vnd.android.package-archive" in source
    assert "application/x-itunes-ipa" in source
    assert 'choices=["apk", "ipa"]' in source
