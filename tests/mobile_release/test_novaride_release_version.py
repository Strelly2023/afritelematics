from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERSION = "2026.1.3"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_novaride_apps_versions_are_2026_1_2() -> None:
    expected_codes = {
        "rider_app": 6,
        "driver_app": 6,
        "novaride_fleet_app": 5,
        "novaride_operator_app": 5,
    }
    for app, expected_code in expected_codes.items():
        config = json.loads(read(f"{app}/app.json"))["expo"]
        gradle = read(f"{app}/android/app/build.gradle")
        package_json = json.loads(read(f"{app}/package.json"))
        assert config["version"] == VERSION
        assert package_json["version"] == VERSION
        assert f'versionName "{VERSION}"' in gradle
        assert int(re.search(r"versionCode\s+(\d+)", gradle).group(1)) >= expected_code
