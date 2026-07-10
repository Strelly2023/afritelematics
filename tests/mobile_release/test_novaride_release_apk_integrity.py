from __future__ import annotations

import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_apk_validation_script_uses_integrity_and_signing_tools() -> None:
    source = (ROOT / "scripts/mobile/verify_apk_artifact.sh").read_text(encoding="utf-8")
    for marker in ["file", "unzip -t", "aapt dump badging", "apksigner verify", "sha256"]:
        assert marker in source
    assert "CN=Android Debug" in source
    assert "debug signing certificate is not allowed" in source


def test_public_pilot_apks_are_valid_zip_when_present() -> None:
    for apk in [
        ROOT / "apk/novaride-rider-v2026.1.1-public-pilot.apk",
        ROOT / "apk/novaride-driver-v2026.1.1-public-pilot.apk",
    ]:
        if apk.exists():
            assert zipfile.is_zipfile(apk)
            assert apk.stat().st_size > 1024 * 1024
