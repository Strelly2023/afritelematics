from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_manifests_define_immutable_and_alias_urls() -> None:
    for name, app in [
        ("novaride_rider_v2026.1.4_manifest.json", "rider"),
        ("novaride_driver_v2026.1.4_manifest.json", "driver"),
    ]:
        manifest = json.loads((ROOT / "docs/mobile/release" / name).read_text(encoding="utf-8"))
        assert manifest["immutable_apk_url"].endswith(
            f"/novaride/releases/2026.1.4/novaride-{app}-v2026.1.4-public-pilot.apk"
        )
        assert manifest["alias_url"].endswith(f"/novaride/{app}-latest-public-pilot.apk")
        assert manifest["ga_allowed"] is False
        assert manifest["real_payments_enabled"] is False
