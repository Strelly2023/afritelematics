from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

CONTROLLED_PILOT_CONFIG_PATH = ROOT / "config/controlled_pilot.json"
PILOT_REGISTRY_PATH = ROOT / "docs/pilot/approved_pilot_registry.json"
BUTTON_REGISTRY_PATH = ROOT / "docs/mobile/controlled_pilot_button_registry.json"
DOWNLOAD_PAGE_PATH = ROOT / "docs/mobile/release/CONTROLLED_PILOT_DOWNLOAD_PAGE.md"

APK_CASES = [
    ("novaride-rider-v2026.1.0-release.apk", "rider_app_release_manifest.json", "AfriRide Rider"),
    ("novaride-driver-v2026.1.0-release.apk", "driver_app_release_manifest.json", "AfriRide Driver"),
    ("novaride-operator-v2026.1.0-release.apk", "operator_dashboard_release_manifest.json", "AfriRide Operator Dashboard"),
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

APP_SOURCE_FILES = {
    "novaride_rider": ["rider_app/App.tsx"],
    "novaride_driver": ["driver_app/App.tsx"],
    "novaride_operator": ["novaride_operator_app/App.tsx"],
    "novapay_consumer": ["novapay_consumer_app/src/appConfig.ts", "novapay_consumer_app/src/roleApp.tsx"],
    "novapay_agent": ["novapay_agent_app/src/agentApp.tsx"],
    "novapay_merchant": ["novapay_merchant_app/src/appConfig.ts", "novapay_merchant_app/src/roleApp.tsx"],
    "novapay_business": ["novapay_business_app/src/appConfig.ts", "novapay_business_app/src/roleApp.tsx"],
    "novaid_personal": ["novaid_personal_app/src/appConfig.ts", "novaid_personal_app/App.tsx"],
    "novaid_business": ["novaid_business_app/src/appConfig.ts", "novaid_business_app/App.tsx"],
    "novaid_employee": ["novaid_employee_app/src/appConfig.ts", "novaid_employee_app/App.tsx"],
    "novaid_partner": ["novaid_partner_app/src/appConfig.ts", "novaid_partner_app/App.tsx"],
    "novaid_inspector": ["novaid_inspector_app/src/appConfig.ts", "novaid_inspector_app/App.tsx"],
}

PILOT_ACCOUNTS = {
    "rider": ("pilot-rider-1", "CUSTOMER", "device-rider-1"),
    "consumer": ("pilot-consumer-1", "CUSTOMER", "device-consumer-1"),
    "driver": ("driver-pilot-1", "DRIVER", "device-rider-1"),
    "operator": ("operator-pilot-1", "OPERATOR", "device-business-1"),
    "agent": ("agent-pilot-1", "DISPATCHER", "device-agent-1"),
    "merchant": ("merchant-pilot-1", "CLIENT", "device-merchant-1"),
    "business": ("business-pilot-1", "CLIENT", "device-business-1"),
    "identity": ("pilot-consumer-1", "VERIFIER", "device-consumer-1"),
}


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def read_json(relative_path: str) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def load_source_text(app_key: str) -> str:
    return "\n".join(read_text(path) for path in APP_SOURCE_FILES[app_key])


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checksum_prefix(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip().split()[0]


def token_payload(user_id: str, role: str) -> dict[str, str]:
    return {"user_id": user_id, "role": role}


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def assert_contains_all(source: str, labels: list[str], *, context: str) -> None:
    missing = [label for label in labels if label not in source]
    assert not missing, f"{context} missing labels: {missing}"
