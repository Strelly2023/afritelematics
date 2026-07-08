from __future__ import annotations

from tests.private_dev._helpers import ROOT, assert_contains_all, read_json, read_text


INTERNAL_QA_CONFIG_PATH = "config/internal_qa.json"
BUTTON_REGISTRY_PATH = "docs/mobile/private_dev_button_registry.json"

APK_CASES = [
    ("novaride-rider-v2026.1.0-release.apk", "rider_app_release_manifest.json", "AfriRide Rider"),
    ("novaride-driver-v2026.1.0-release.apk", "driver_app_release_manifest.json", "AfriRide Driver"),
    (
        "novaride-operator-v2026.1.0-release.apk",
        "operator_dashboard_release_manifest.json",
        "AfriRide Operator Dashboard",
    ),
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
