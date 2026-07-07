from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tests.private_dev._helpers import ROOT, read_json


pytestmark = [pytest.mark.private_dev, pytest.mark.apk, pytest.mark.release_guard]


APK_CASES = [
    ("novaride-rider-v2026.1.0-release.apk", "rider_app_release_manifest.json", "AfriRide Rider"),
    ("novaride-driver-v2026.1.0-release.apk", "driver_app_release_manifest.json", "AfriRide Driver"),
    ("novaride-operator-v2026.1.0-release.apk", "operator_dashboard_release_manifest.json", "AfriRide Operator Dashboard"),
    ("novapay-consumer-v2026.1.0-release.apk", "novapay_consumer_app_release_manifest.json", "NovaPay Consumer App"),
    ("novapay-agent-v2026.1.0-release.apk", "novapay_agent_app_release_manifest.json", "NovaPay Agent App"),
    ("novapay-merchant-v2026.1.0-release.apk", "novapay_merchant_app_release_manifest.json", "NovaPay Merchant App"),
    ("novapay-business-v2026.1.0-release.apk", "novapay_business_app_release_manifest.json", "NovaPay Business App"),
    ("novaid-personal-v2026.1.0-release.apk", "novaid_personal_app_release_manifest.json", "NovaID Personal App"),
    ("novaid-business-v2026.1.0-release.apk", "novaid_business_app_release_manifest.json", "NovaID Business App"),
    ("novaid-employee-v2026.1.0-release.apk", "novaid_employee_app_release_manifest.json", "NovaID Employee App"),
    ("novaid-partner-v2026.1.0-release.apk", "novaid_partner_app_release_manifest.json", "NovaID Partner App"),
    ("novaid-inspector-v2026.1.0-release.apk", "novaid_inspector_app_release_manifest.json", "NovaID Inspector App"),
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_checksum(path: Path) -> str:
    content = path.read_text(encoding="utf-8").strip()
    return content.split()[0]


def test_required_apks_checksums_and_manifests_exist() -> None:
    config = read_json("config/private_development.json")
    assert config["environment"] == "PRIVATE_DEVELOPMENT"
    assert config["live_payments_enabled"] is False
    assert config["real_charging_enabled"] is False

    for apk_name, manifest_name, app_name in APK_CASES:
        apk_path = ROOT / "apk" / apk_name
        checksum_path = ROOT / "apk" / f"{apk_name}.sha256"
        manifest_path = ROOT / "docs/mobile/release" / manifest_name

        assert apk_path.is_file(), f"missing apk artifact: {apk_path}"
        assert checksum_path.is_file(), f"missing checksum artifact: {checksum_path}"
        assert manifest_path.is_file(), f"missing release manifest: {manifest_path}"

        expected_hash = _sha256(apk_path)
        recorded_hash = _read_checksum(checksum_path)
        assert recorded_hash == expected_hash, f"checksum mismatch for {apk_name}"

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert app_name in manifest["display_name"]
        assert manifest["version_name"] == "2026.1.0"
        assert isinstance(manifest["version_code"], int)
        assert manifest["version_code"] > 0
        assert manifest["release_channel"] != "production"
