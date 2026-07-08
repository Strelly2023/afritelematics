from __future__ import annotations

from pathlib import Path

import pytest

from tests.internal_qa._helpers import ROOT


pytestmark = [pytest.mark.internal_qa, pytest.mark.qa_icons, pytest.mark.mobile]


APP_ICON_CASES = {
    "rider_app": "AfriRide Rider",
    "driver_app": "AfriRide Driver",
    "novaride_operator_app": "AfriRide Operator Dashboard",
    "novapay_consumer_app": "NovaPay Consumer App",
    "novapay_agent_app": "NovaPay Agent App",
    "novapay_merchant_app": "NovaPay Merchant App",
    "novapay_business_app": "NovaPay Business App",
    "novaid_personal_app": "NovaID Personal App",
    "novaid_business_app": "NovaID Business App",
    "novaid_employee_app": "NovaID Employee App",
    "novaid_partner_app": "NovaID Partner App",
    "novaid_inspector_app": "NovaID Inspector App",
}

ICON_SUFFIXES = [
    "mipmap-mdpi/ic_launcher.png",
    "mipmap-hdpi/ic_launcher.png",
    "mipmap-xhdpi/ic_launcher.png",
    "mipmap-xxhdpi/ic_launcher.png",
    "mipmap-xxxhdpi/ic_launcher.png",
    "mipmap-anydpi-v26/ic_launcher.xml",
    "mipmap-anydpi-v26/ic_launcher_round.xml",
]


def test_internal_qa_android_icons_exist_and_are_referenced() -> None:
    for app_dir, app_label in APP_ICON_CASES.items():
        manifest_path = ROOT / app_dir / "android/app/src/main/AndroidManifest.xml"
        manifest_text = manifest_path.read_text(encoding="utf-8")
        assert app_label in (ROOT / f"docs/mobile/release/{_manifest_name(app_dir)}").read_text(encoding="utf-8")
        assert "ic_launcher" in manifest_text
        for suffix in ICON_SUFFIXES:
            icon_path = ROOT / app_dir / "android/app/src/main/res" / suffix
            assert icon_path.is_file(), f"missing icon asset: {icon_path}"
            assert icon_path.stat().st_size > 0, f"empty icon asset: {icon_path}"


def _manifest_name(app_dir: str) -> str:
    return {
        "rider_app": "rider_app_release_manifest.json",
        "driver_app": "driver_app_release_manifest.json",
        "novaride_operator_app": "operator_dashboard_release_manifest.json",
        "novapay_consumer_app": "novapay_consumer_app_release_manifest.json",
        "novapay_agent_app": "novapay_agent_app_release_manifest.json",
        "novapay_merchant_app": "novapay_merchant_app_release_manifest.json",
        "novapay_business_app": "novapay_business_app_release_manifest.json",
        "novaid_personal_app": "novaid_personal_app_release_manifest.json",
        "novaid_business_app": "novaid_business_app_release_manifest.json",
        "novaid_employee_app": "novaid_employee_app_release_manifest.json",
        "novaid_partner_app": "novaid_partner_app_release_manifest.json",
        "novaid_inspector_app": "novaid_inspector_app_release_manifest.json",
    }[app_dir]
