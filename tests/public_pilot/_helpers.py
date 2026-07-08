from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

PUBLIC_PILOT_CONFIG_PATH = ROOT / "config/public_pilot.json"
PUBLIC_PILOT_APPROVAL_PATH = ROOT / "docs/public_pilot/PUBLIC_PILOT_APPROVAL.json"
PUBLIC_PILOT_EXIT_REPORT_PATH = ROOT / "docs/public_pilot/PUBLIC_PILOT_EXIT_REPORT.yaml"
PUBLIC_PILOT_IMPLEMENTATION_PATH = ROOT / "docs/public_pilot/PUBLIC_PILOT_IMPLEMENTATION.md"
PUBLIC_PILOT_DOWNLOAD_PAGE_PATH = ROOT / "docs/public_pilot/PUBLIC_PILOT_DOWNLOAD_PAGE.md"
PUBLIC_PILOT_MONITORING_PATH = ROOT / "docs/public_pilot/PUBLIC_PILOT_MONITORING.md"
PUBLIC_PILOT_BUTTON_REGISTRY_PATH = ROOT / "docs/mobile/public_pilot_button_registry.json"
PUBLIC_PILOT_APK_MANIFESTS_PATH = ROOT / "docs/public_pilot/PUBLIC_PILOT_APK_RELEASE_MANIFESTS.json"
PRR_PATH = ROOT / "docs/prr/PRR-001-production-readiness-review.yaml"

APK_CASES = [
    ("novaride-rider-public-pilot-release.apk", "novaride-rider-v2026.1.0-release.apk", "59955032bac42f92e612af8002dbfd80e555f6644f54a10d7792d535ed8d2e35"),
    ("novaride-driver-public-pilot-release.apk", "novaride-driver-v2026.1.0-release.apk", "b594204c13d9d2a8d1bf35658b60207dc5ce62768d0bbff08105928c6cbd3507"),
    ("novaride-fleet-public-pilot-release.apk", "novaride-fleet-v2026.1.0-release.apk", "0c0592eac2d5b331ab2f3b3a077a296bb60ca8583e1113068acf42c401307d4d"),
    ("novaride-operator-public-pilot-release.apk", "novaride-operator-v2026.1.0-release.apk", "a31b97809c80e1964c3862b75d592a4603e256e76b4030749d2f2bb5cbf7391b"),
    ("novapay-consumer-public-pilot-release.apk", "novapay-consumer-v2026.1.0-release.apk", "f7a8e502f39c369d569deaa8cac1c51d52e89666a747a62af9d2fa13e4c33f85"),
    ("novapay-agent-public-pilot-release.apk", "novapay-agent-v2026.1.0-release.apk", "e1d86c6bbca896cab6452d43d1297d47e302a9aa9b98497624831a83d7696b42"),
    ("novapay-merchant-public-pilot-release.apk", "novapay-merchant-v2026.1.0-release.apk", "86549490c5c2f69ca50c7e467e7b9751e430453319fa282517a1104543f22aa2"),
    ("novapay-business-public-pilot-release.apk", "novapay-business-v2026.1.0-release.apk", "51b1cabb6552d618049a91c1954dc6edd914aac812086dd4640063c60e107ee6"),
    ("novaid-personal-public-pilot-release.apk", "novaid-personal-v2026.1.0-release.apk", "249ac445c91b463d9b148d892a49057b0e97a045b912d4c8677e681b8656d21c"),
    ("novaid-business-public-pilot-release.apk", "novaid-business-v2026.1.0-release.apk", "b64d06066aa8bfe66063d207242d0255dea18509d5fcf48f7d202e4a00f78ec8"),
    ("novaid-employee-public-pilot-release.apk", "novaid-employee-v2026.1.0-release.apk", "49941dd547fafde569ebbe50094730296686057403ea8ba823c49089fb1741ba"),
    ("novaid-partner-public-pilot-release.apk", "novaid-partner-v2026.1.0-release.apk", "bf8434bde0346aebae7adad7a045e20370f3d971828c0deea194c4ba642c538b"),
    ("novaid-inspector-public-pilot-release.apk", "novaid-inspector-v2026.1.0-release.apk", "e727e3eba2de1d11fd384affecec616abb3520c6f5442c3e1cc905e7021cbd36"),
]

APP_SOURCE_FILES = {
    "novaride_rider": ["rider_app/App.tsx"],
    "novaride_driver": ["driver_app/App.tsx"],
    "novaride_operator": ["novaride_operator_app/App.tsx"],
    "novaride_fleet": ["novaride_fleet_app/App.tsx"],
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

PUBLIC_PILOT_ACCOUNTS = {
    "rider": ("public-rider-1", "CUSTOMER", "public-device-rider-1", "Melbourne"),
    "driver": ("public-driver-1", "DRIVER", "public-device-driver-1", "Melbourne"),
    "operator": ("public-operator-1", "OPERATOR", "public-device-operator-1", "Melbourne"),
    "consumer": ("public-consumer-1", "CUSTOMER", "public-device-consumer-1", "Melbourne"),
    "agent": ("public-agent-1", "DISPATCHER", "public-device-agent-1", "Melbourne"),
    "merchant": ("public-merchant-1", "CLIENT", "public-device-merchant-1", "Melbourne"),
    "business": ("public-business-1", "CLIENT", "public-device-business-1", "Melbourne"),
    "employee": ("public-employee-1", "OBSERVER", "public-device-employee-1", "Melbourne"),
    "identity": ("public-verifier-1", "VERIFIER", "public-device-verifier-1", "Melbourne"),
    "partner": ("public-partner-1", "PARTNER", "public-device-partner-1", "Melbourne"),
    "inspector": ("public-inspector-1", "OBSERVER", "public-device-inspector-1", "Melbourne"),
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


def public_pilot_approval_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "public_pilot_approved": True,
        "approval_id": "ppa-001",
        "approved_by": "public.pilot@novatech.test",
        "approved_at": "2026-07-08T00:00:00Z",
        "scope": "PUBLIC_PILOT_ONLY",
        "approved_regions": ["Melbourne"],
        "approved_user_limit": 25,
        "limited_real_payments_approved": True,
        "real_identity_onboarding_approved": True,
        "real_ride_requests_approved": True,
        "public_pilot_live_payment_approved": True,
        "max_transaction_amount_aud": 50,
        "daily_transaction_limit_aud": 200,
        "monthly_transaction_limit_aud": 1000,
        "ga_enabled": False,
        "production_readiness_review_required": True,
        "rollback_plan_approved": True,
        "incident_response_approved": True,
        "support_operations_approved": True,
        "monitoring_verified": True,
        "compliance_verified": True,
        "approved_users": [
            PUBLIC_PILOT_ACCOUNTS["rider"][0],
            PUBLIC_PILOT_ACCOUNTS["driver"][0],
            PUBLIC_PILOT_ACCOUNTS["operator"][0],
            PUBLIC_PILOT_ACCOUNTS["consumer"][0],
            PUBLIC_PILOT_ACCOUNTS["agent"][0],
            PUBLIC_PILOT_ACCOUNTS["merchant"][0],
            PUBLIC_PILOT_ACCOUNTS["business"][0],
            PUBLIC_PILOT_ACCOUNTS["employee"][0],
            PUBLIC_PILOT_ACCOUNTS["identity"][0],
            PUBLIC_PILOT_ACCOUNTS["partner"][0],
            PUBLIC_PILOT_ACCOUNTS["inspector"][0],
        ],
        "approved_devices": [
            PUBLIC_PILOT_ACCOUNTS["rider"][2],
            PUBLIC_PILOT_ACCOUNTS["driver"][2],
            PUBLIC_PILOT_ACCOUNTS["operator"][2],
            PUBLIC_PILOT_ACCOUNTS["consumer"][2],
            PUBLIC_PILOT_ACCOUNTS["agent"][2],
            PUBLIC_PILOT_ACCOUNTS["merchant"][2],
            PUBLIC_PILOT_ACCOUNTS["business"][2],
            PUBLIC_PILOT_ACCOUNTS["employee"][2],
            PUBLIC_PILOT_ACCOUNTS["identity"][2],
            PUBLIC_PILOT_ACCOUNTS["partner"][2],
            PUBLIC_PILOT_ACCOUNTS["inspector"][2],
        ],
        "approved_drivers": [PUBLIC_PILOT_ACCOUNTS["driver"][0]],
        "approved_operators": [PUBLIC_PILOT_ACCOUNTS["operator"][0]],
        "approved_agents": [PUBLIC_PILOT_ACCOUNTS["agent"][0]],
        "approved_merchants": [PUBLIC_PILOT_ACCOUNTS["merchant"][0]],
        "approved_businesses": [PUBLIC_PILOT_ACCOUNTS["business"][0]],
    }
    payload.update(overrides)
    return payload
