from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_release_provenance_exists_for_rider_and_driver() -> None:
    data = json.loads(
        (ROOT / "reports/mobile/releases/2026.1.4/novaride-release-provenance.json").read_text(
            encoding="utf-8"
        )
    )
    assert data["release"] == "2026.1.4"
    for app in ("rider", "driver"):
        assert data[app]["version"] == "2026.1.4"
        assert data[app]["versionCode"] >= 7
        assert data[app]["apiHost"] == "https://api.afritechnology.com"
        assert data[app]["publicationUrl"].startswith("https://download.afritechnology.com/")
        assert data[app]["apkSha256"] != "pending-release-build"
        assert len(data[app]["apkSha256"]) == 64
        assert data[app]["apkByteSize"] > 1_000_000
        assert data[app]["signingVerificationStatus"] == "required_before_publication"


def test_release_provenance_has_real_build_identity() -> None:
    data = json.loads(
        (ROOT / "reports/mobile/releases/2026.1.4/novaride-release-provenance.json").read_text(
            encoding="utf-8"
        )
    )
    for key in ("generated_at", "builder", "branch", "commit", "workflow_run"):
        assert data[key] not in {"", "pending-release-build", "unknown"}
