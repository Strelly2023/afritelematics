from __future__ import annotations

from pathlib import Path

import pytest

from tests.public_pilot._helpers import ROOT, read_json


pytestmark = [pytest.mark.public_pilot, pytest.mark.pilot_apk]


ICON_FILES = (
    "android/app/src/main/res/mipmap-mdpi/ic_launcher.png",
    "android/app/src/main/res/mipmap-hdpi/ic_launcher.png",
    "android/app/src/main/res/mipmap-xhdpi/ic_launcher.png",
    "android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png",
    "android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png",
    "android/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml",
    "android/app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml",
)

APP_PATHS = (
    "rider_app",
    "driver_app",
    "novaride_operator_app",
    "novaride_fleet_app",
    "novapay_consumer_app",
    "novapay_agent_app",
    "novapay_merchant_app",
    "novapay_business_app",
    "novaid_personal_app",
    "novaid_business_app",
    "novaid_employee_app",
    "novaid_partner_app",
    "novaid_inspector_app",
)


def test_public_pilot_android_icons_exist_for_each_app() -> None:
    for app_path in APP_PATHS:
        for rel in ICON_FILES:
            path = ROOT / app_path / rel
            assert path.exists(), path
            assert path.stat().st_size > 0, path


def test_public_pilot_android_labels_and_manifest_references_are_present() -> None:
    labels = {
        "rider_app": "NovaRide Rider",
        "driver_app": "NovaRide Driver",
        "novaride_operator_app": "NovaRide Operator",
        "novaride_fleet_app": "NovaRide Fleet",
        "novapay_consumer_app": "NovaPay Consumer",
        "novapay_agent_app": "NovaPay Agent",
        "novapay_merchant_app": "NovaPay Merchant",
        "novapay_business_app": "NovaPay Business",
        "novaid_personal_app": "NovaID Personal",
        "novaid_business_app": "NovaID Business",
        "novaid_employee_app": "NovaID Employee",
        "novaid_partner_app": "NovaID Partner",
        "novaid_inspector_app": "NovaID Inspector",
    }
    for app_path, label in labels.items():
        strings = ROOT / app_path / "android/app/src/main/res/values/strings.xml"
        app_json = ROOT / app_path / "app.json"
        if strings.exists():
            assert label in strings.read_text(encoding="utf-8")
        if app_json.exists():
            payload = read_json(f"{app_path}/app.json")
            assert label in str(payload)
