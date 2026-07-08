from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.controlled_pilot._helpers import APK_CASES, DOWNLOAD_PAGE_PATH, ROOT, checksum_prefix, read_json, sha256_file


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_apk, pytest.mark.apk]


def test_controlled_pilot_apks_checksums_manifests_and_labels_exist() -> None:
    config = read_json("config/controlled_pilot.json")
    assert config["environment"] == "CONTROLLED_PILOT"
    assert config["payment_mode"] == "SIMULATED"
    assert config["live_payments_enabled"] is False

    for apk_name, manifest_name, app_label in APK_CASES:
        apk_path = ROOT / "apk" / apk_name
        checksum_path = ROOT / "apk" / f"{apk_name}.sha256"
        manifest_path = ROOT / "docs/mobile/release" / manifest_name

        assert apk_path.is_file(), f"missing apk artifact: {apk_path}"
        assert checksum_path.is_file(), f"missing checksum artifact: {checksum_path}"
        assert manifest_path.is_file(), f"missing release manifest: {manifest_path}"

        assert checksum_prefix(checksum_path) == sha256_file(apk_path), f"checksum mismatch for {apk_name}"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["display_name"]
        assert app_label in manifest["display_name"]
        assert manifest["version_name"] == "2026.1.0"
        assert isinstance(manifest["version_code"], int)
        assert manifest["version_code"] > 0
        assert manifest["release_channel"] in {"controlled_pilot_to_store", "internal_operator_web"}
        assert "production" not in manifest["release_channel"].lower()
        assert "debug" not in manifest["display_name"].lower()
        assert manifest["apk_url"].endswith(apk_name)
        if "android_package" in manifest["store_surfaces"]:
            assert manifest["store_surfaces"]["android_package"]
        else:
            assert manifest["store_surfaces"]["distribution"] == "private_operator_url"
            assert manifest["store_surfaces"]["public_store_listing"] is False
        assert manifest["release_artifacts"]["android_apk"].endswith(apk_name)


def test_controlled_pilot_download_page_is_explicit() -> None:
    source = DOWNLOAD_PAGE_PATH.read_text(encoding="utf-8")
    assert "Controlled Pilot APK Download Page" in source
    assert "Controlled pilot only. Not public launch. Not general availability." in source
