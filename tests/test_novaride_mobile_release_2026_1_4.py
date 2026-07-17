from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_shared_secure_session_is_app_scoped() -> None:
    source = read("afriride_system/mobile/shared/secureSession.js")
    rider = read("rider_app/core/api/session.ts")
    driver = read("driver_app/core/api/session.ts")

    assert "tokenKey(app)" in source
    assert "sessionKey(app)" in source
    assert "memoryTokens" in source
    assert 'const APP_NAME = "rider"' in rider
    assert 'const APP_NAME = "driver"' in driver
    assert "clearAppSession" in rider
    assert "clearAppSession" in driver
    assert "restoreAppSession" in rider
    assert "restoreAppSession" in driver


def test_2026_1_4_release_manifests_and_scripts_are_aligned() -> None:
    rider_manifest = json.loads(
        read("docs/mobile/release/novaride_rider_v2026.1.4_manifest.json")
    )
    driver_manifest = json.loads(
        read("docs/mobile/release/novaride_driver_v2026.1.4_manifest.json")
    )
    publish = read("scripts/mobile/publish_novaride_release.sh")
    metadata = read("scripts/mobile/generate_release_metadata.py")

    assert rider_manifest["release_version"] == "2026.1.4"
    assert driver_manifest["release_version"] == "2026.1.4"
    assert rider_manifest["android_versionCode"] == 7
    assert driver_manifest["android_versionCode"] == 7
    assert "2026.1.4" in publish
    assert '"rider": 7' in metadata
    assert '"driver": 7' in metadata
