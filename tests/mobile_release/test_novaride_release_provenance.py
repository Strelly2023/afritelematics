from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_release_provenance_exists_for_rider_and_driver() -> None:
    data = json.loads(
        (ROOT / "reports/mobile/releases/2026.1.3/novaride-release-provenance.json").read_text(
            encoding="utf-8"
        )
    )
    assert data["release"] == "2026.1.3"
    for app in ("rider", "driver", "fleet", "operator"):
        assert data[app]["version"] == "2026.1.3"
        assert data[app]["versionCode"] >= 4
        assert data[app]["apiHost"] == "https://api.afritechnology.com"
        assert data[app]["publicationUrl"].startswith("https://download.afritechnology.com/")
