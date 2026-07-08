from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tests.internal_qa._helpers import APK_CASES, INTERNAL_QA_CONFIG_PATH, ROOT, read_json


pytestmark = [pytest.mark.internal_qa, pytest.mark.qa_apk, pytest.mark.qa_release_guard, pytest.mark.apk]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_checksum(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip().split()[0]


def test_internal_qa_required_apks_checksums_and_manifests_exist() -> None:
    config = read_json(INTERNAL_QA_CONFIG_PATH)
    assert config["environment"] == "INTERNAL_QA"
    assert config["live_payments_enabled"] is False
    assert config["real_charging_enabled"] is False
    assert config["external_payouts_enabled"] is False

    for apk_name, manifest_name, app_name in APK_CASES:
        apk_path = ROOT / "apk" / apk_name
        checksum_path = ROOT / "apk" / f"{apk_name}.sha256"
        manifest_path = ROOT / "docs/mobile/release" / manifest_name

        assert apk_path.is_file(), f"missing apk artifact: {apk_path}"
        assert checksum_path.is_file(), f"missing checksum artifact: {checksum_path}"
        assert manifest_path.is_file(), f"missing release manifest: {manifest_path}"

        assert _read_checksum(checksum_path) == _sha256(apk_path), f"checksum mismatch for {apk_name}"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert app_name in manifest["display_name"]
        assert manifest["version_name"]
        assert isinstance(manifest["version_code"], int)
        assert manifest["version_code"] > 0
        assert manifest["release_channel"] != "production"
        assert "debug" not in manifest["display_name"].lower()
        assert manifest.get("environment", config["environment"]) in {"INTERNAL_QA", "INTERNAL_ONLY"}
