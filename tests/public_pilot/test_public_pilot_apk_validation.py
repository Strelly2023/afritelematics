from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.public_pilot._helpers import APK_CASES, PUBLIC_PILOT_APK_MANIFESTS_PATH, ROOT, checksum_prefix, read_json, sha256_file


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_release_guard, pytest.mark.pilot_apk]


def test_public_pilot_apk_artifacts_exist_and_match_hashes() -> None:
    manifests = read_json("docs/public_pilot/PUBLIC_PILOT_APK_RELEASE_MANIFESTS.json")
    apps = manifests["apps"]
    assert manifests["environment"] == "PUBLIC_PILOT"
    assert manifests["ga_enabled"] is False
    assert manifests["production_claim_allowed"] is False
    assert len(apps) == len(APK_CASES)

    for app in apps:
        apk_path = ROOT / "apk" / app["apk_file"]
        sha_path = ROOT / "apk" / f"{app['apk_file']}.sha256"
        assert apk_path.exists(), apk_path
        assert sha_path.exists(), sha_path
        assert sha256_file(apk_path) == checksum_prefix(sha_path)
        assert app["version_name"] == "2026.1.0"
        assert app["environment"] == "PUBLIC_PILOT"
        assert app["ga_enabled"] is False
        assert "production" not in json.dumps(app).lower() or "production_claim_allowed" in app


def test_public_pilot_apk_download_page_mentions_public_pilot() -> None:
    page = (ROOT / "docs/public_pilot/PUBLIC_PILOT_DOWNLOAD_PAGE.md").read_text(encoding="utf-8")
    assert "Public Pilot" in page
    assert "APK" in page
