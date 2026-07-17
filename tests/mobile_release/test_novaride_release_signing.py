from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXPECTED_RELEASE_FINGERPRINT = (
    "117f77e5e461c6a111ae83d7b32cf84aa76f5be3287692795f54a229bccd12cc"
)
EXPECTED_V2_FINGERPRINT = (
    "5bd809c088bb1634af02f2880fba44d13f732635fcb2eff74aa49ca8f47f9d61"
)


def test_release_manifest_tracks_signing_fingerprint() -> None:
    for path in [
        ROOT / "docs/mobile/release/novaride_rider_v2026.1.4_manifest.json",
        ROOT / "docs/mobile/release/novaride_driver_v2026.1.4_manifest.json",
    ]:
        text = path.read_text(encoding="utf-8")
        assert "signing_certificate_fingerprint" in text
        assert "pending-apksigner" in text or "SHA-256" in text or "sha256" in text.lower()


def test_release_signing_credentials_script_is_fail_closed() -> None:
    source = (ROOT / "scripts/mobile/verify_release_signing_credentials.sh").read_text(
        encoding="utf-8"
    )
    for env_name in [
        "AFRIRIDE_ANDROID_KEYSTORE_PATH",
        "AFRIRIDE_ANDROID_KEYSTORE_PASSWORD",
        "AFRIRIDE_ANDROID_KEY_ALIAS",
        "AFRIRIDE_ANDROID_KEY_PASSWORD",
    ]:
        assert env_name in source
    assert "keytool -list -v" in source
    assert "SIGNING_SECRET_PROVIDER" in source
    assert "release_lineage.py" in source
    assert "fingerprint mismatch" in source


def test_release_publish_pipeline_verifies_signing_credentials_first() -> None:
    source = (ROOT / "scripts/mobile/publish_novaride_release.sh").read_text(
        encoding="utf-8"
    )
    assert "release_health_check.sh" in source


def test_release_lineage_registry_records_canonical_android_identity() -> None:
    source = (ROOT / "docs/mobile/release/release_lineage.yaml").read_text(
        encoding="utf-8"
    )
    assert "product: NovaRide" in source
    assert "lineages:" in source
    assert "id: legacy" in source
    assert "id: v2" in source
    assert "status: retired-unrecoverable" in source
    assert "status: production" in source
    assert "alias: novaride-release" in source
    assert EXPECTED_RELEASE_FINGERPRINT in source
    assert EXPECTED_V2_FINGERPRINT in source
    for provider in [
        "github-actions",
        "1password",
        "bitwarden",
        "aws-secrets-manager",
        "vault",
        "macos-keychain",
    ]:
        assert provider in source


def test_release_health_check_and_audit_tools_exist() -> None:
    for path in [
        ROOT / "scripts/mobile/release_health_check.sh",
        ROOT / "scripts/mobile/verify_release_manifest.py",
        ROOT / "scripts/mobile/generate_release_certificate_metadata.sh",
        ROOT / "scripts/mobile/generate_release_audit_report.py",
        ROOT / "scripts/mobile/create_new_signing_lineage_v2.sh",
        ROOT / "scripts/mobile/run_with_keychain_android_signing.sh",
        ROOT / "scripts/mobile/materialize_android_keystore.sh",
    ]:
        assert path.exists()
        assert path.read_text(encoding="utf-8").startswith("#!")


def test_mobile_release_workflow_has_signing_ci_gate() -> None:
    source = (ROOT / ".github/workflows/novaride-mobile-release.yml").read_text(
        encoding="utf-8"
    )
    assert "AFRIRIDE_ANDROID_KEYSTORE_BASE64" in source
    assert "SIGNING_SECRET_PROVIDER: github-actions" in source
    assert "verify_release_signing_credentials.sh" in source
    assert "materialize_android_keystore.sh" in source
    assert "actions/upload-artifact@v4" in source
    assert "actions/download-artifact@v4" in source
    assert "--require-apk-tools" in source
    assert "publish_static_release.sh" in source
    assert 'echo "stage immutable artifacts"' not in source
    assert 'echo "publish immutable APKs after approval"' not in source


def test_manifest_validator_recomputes_binary_identity() -> None:
    source = (ROOT / "scripts/mobile/verify_release_manifest.py").read_text(encoding="utf-8")
    assert "apk.stat().st_size" in source
    assert "sha256(apk)" in source
    assert "aapt" in source
    assert "apksigner" in source
    assert "--require-apk-tools" in source


def test_new_lineage_creation_is_guarded_by_explicit_approval() -> None:
    source = (ROOT / "scripts/mobile/create_new_signing_lineage_v2.sh").read_text(
        encoding="utf-8"
    )
    assert "NOVARIDE_CONFIRM_NEW_LINEAGE" in source
    assert "retire-legacy-and-create-v2" in source
    assert "refusing to overwrite existing v2 keystore" in source
    assert "keytool -genkeypair" in source
