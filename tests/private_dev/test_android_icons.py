from __future__ import annotations

import pytest

from tests.private_dev._helpers import ROOT


pytestmark = [pytest.mark.private_dev, pytest.mark.local_only]


APP_ICON_ROOTS = [
    "rider_app/android/app/src/main/res",
    "driver_app/android/app/src/main/res",
    "novaride_operator_app/android/app/src/main/res",
    "novapay_consumer_app/android/app/src/main/res",
    "novapay_agent_app/android/app/src/main/res",
    "novapay_merchant_app/android/app/src/main/res",
    "novapay_business_app/android/app/src/main/res",
    "novaid_personal_app/android/app/src/main/res",
    "novaid_business_app/android/app/src/main/res",
    "novaid_employee_app/android/app/src/main/res",
    "novaid_partner_app/android/app/src/main/res",
    "novaid_inspector_app/android/app/src/main/res",
]


def test_all_android_launcher_icons_exist() -> None:
    required = [
        "mipmap-mdpi/ic_launcher.png",
        "mipmap-hdpi/ic_launcher.png",
        "mipmap-xhdpi/ic_launcher.png",
        "mipmap-xxhdpi/ic_launcher.png",
        "mipmap-xxxhdpi/ic_launcher.png",
        "mipmap-anydpi-v26/ic_launcher.xml",
        "mipmap-anydpi-v26/ic_launcher_round.xml",
    ]
    missing: list[str] = []
    for root in APP_ICON_ROOTS:
        for item in required:
            path = ROOT / root / item
            if not path.is_file():
                missing.append(str(path))
    assert not missing, f"missing Android icon assets: {missing}"
