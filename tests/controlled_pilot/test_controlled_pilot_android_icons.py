from __future__ import annotations

from pathlib import Path

import pytest

from tests.controlled_pilot._helpers import ROOT, read_json


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_apk]


ICON_FILES = [
    "mipmap-mdpi/ic_launcher.png",
    "mipmap-hdpi/ic_launcher.png",
    "mipmap-xhdpi/ic_launcher.png",
    "mipmap-xxhdpi/ic_launcher.png",
    "mipmap-xxxhdpi/ic_launcher.png",
    "mipmap-anydpi-v26/ic_launcher.xml",
    "mipmap-anydpi-v26/ic_launcher_round.xml",
]


def test_controlled_pilot_android_icons_exist_for_each_app() -> None:
    for app_dir in [
        "rider_app",
        "driver_app",
        "novaride_operator_app",
        "novapay_consumer_app",
        "novapay_agent_app",
        "novapay_merchant_app",
        "novapay_business_app",
        "novaid_personal_app",
        "novaid_business_app",
        "novaid_employee_app",
        "novaid_partner_app",
        "novaid_inspector_app",
    ]:
        root = ROOT / app_dir / "android/app/src/main/res"
        for relative in ICON_FILES:
            path = root / relative
            assert path.is_file(), f"missing icon asset: {path}"
            assert path.stat().st_size > 0, f"empty icon asset: {path}"


def test_controlled_pilot_android_labels_and_manifest_references_are_present() -> None:
    for app_dir in [
        "rider_app",
        "driver_app",
        "novaride_operator_app",
        "novapay_consumer_app",
        "novapay_agent_app",
        "novapay_merchant_app",
        "novapay_business_app",
        "novaid_personal_app",
        "novaid_business_app",
        "novaid_employee_app",
        "novaid_partner_app",
        "novaid_inspector_app",
    ]:
        app_json = read_json(f"{app_dir}/app.json")
        manifest = (ROOT / app_dir / "android/app/src/main/AndroidManifest.xml").read_text(encoding="utf-8")
        label = app_json["expo"]["name"]
        assert label in manifest or label in (ROOT / app_dir / "android/app/src/main/res/values/strings.xml").read_text(encoding="utf-8")
        assert "ic_launcher" in manifest
