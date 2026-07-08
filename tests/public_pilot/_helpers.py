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

PUBLIC_PILOT_APPROVED_LOCATIONS = [
    "Melbourne CBD",
    "Docklands",
    "Southbank",
    "Footscray",
    "Sunshine",
    "Werribee",
    "Tarneit",
    "Truganina",
    "Hoppers Crossing",
    "Wyndham Vale",
    "Point Cook",
    "Melton",
    "Caroline Springs",
    "Brisbane CBD",
    "South Brisbane",
    "Fortitude Valley",
    "Logan",
    "Ipswich",
]

PUBLIC_PILOT_APPROVED_REGIONS = [*PUBLIC_PILOT_APPROVED_LOCATIONS, "Melbourne"]

PUBLIC_PILOT_PARTICIPANTS = {
    "drivers": [f"public-driver-{index:03d}" for index in range(1, 11)],
    "riders": [f"public-rider-{index:03d}" for index in range(1, 31)],
    "merchants": [f"public-merchant-{index:03d}" for index in range(1, 3)],
    "agents": [f"public-agent-{index:03d}" for index in range(1, 4)],
    "businesses": [f"public-business-{index:03d}" for index in range(1, 3)],
    "employees": [f"public-employee-{index:03d}" for index in range(1, 11)],
}

PUBLIC_PILOT_DEVICE_BINDINGS = {
    "public-device-001": "public-driver-001",
    "public-device-002": "public-driver-002",
    "public-device-003": "public-driver-003",
    "public-device-004": "public-driver-004",
    "public-device-005": "public-driver-005",
    "public-device-006": "public-driver-006",
    "public-device-007": "public-driver-007",
    "public-device-008": "public-driver-008",
    "public-device-009": "public-driver-009",
    "public-device-010": "public-driver-010",
    "public-device-011": "public-rider-001",
    "public-device-012": "public-rider-002",
    "public-device-013": "public-rider-003",
    "public-device-014": "public-rider-004",
    "public-device-015": "public-rider-005",
    "public-device-016": "public-rider-006",
    "public-device-017": "public-rider-007",
    "public-device-018": "public-rider-008",
    "public-device-019": "public-rider-009",
    "public-device-020": "public-rider-010",
    "public-device-021": "public-rider-011",
    "public-device-022": "public-rider-012",
    "public-device-023": "public-rider-013",
    "public-device-024": "public-rider-014",
    "public-device-025": "public-rider-015",
    "public-device-026": "public-rider-016",
    "public-device-027": "public-rider-017",
    "public-device-028": "public-rider-018",
    "public-device-029": "public-merchant-001",
    "public-device-030": "public-merchant-002",
    "public-device-031": "public-agent-001",
    "public-device-032": "public-agent-002",
    "public-device-033": "public-agent-003",
    "public-device-034": "public-business-001",
    "public-device-035": "public-business-002",
    "public-device-036": "public-employee-001",
    "public-device-037": "public-employee-002",
    "public-device-038": "public-employee-003",
    "public-device-039": "public-employee-004",
    "public-device-040": "public-employee-005",
}

PUBLIC_PILOT_ACCOUNTS = {
    "rider": ("public-rider-001", "CUSTOMER", "public-device-011", "Melbourne CBD"),
    "driver": ("public-driver-001", "DRIVER", "public-device-001", "Melbourne CBD"),
    "operator": ("public-business-001", "OPERATOR", "public-device-034", "Melbourne CBD"),
    "consumer": ("public-rider-002", "CUSTOMER", "public-device-012", "Melbourne CBD"),
    "agent": ("public-agent-001", "DISPATCHER", "public-device-031", "Melbourne CBD"),
    "merchant": ("public-merchant-001", "CLIENT", "public-device-029", "Melbourne CBD"),
    "business": ("public-business-002", "CLIENT", "public-device-035", "Melbourne CBD"),
    "employee": ("public-employee-001", "OBSERVER", "public-device-036", "Melbourne CBD"),
    "identity": ("public-employee-002", "VERIFIER", "public-device-037", "Melbourne CBD"),
    "partner": ("public-employee-003", "PARTNER", "public-device-038", "Melbourne CBD"),
    "inspector": ("public-employee-004", "OBSERVER", "public-device-039", "Melbourne CBD"),
}


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


def _approved_user_ids() -> list[str]:
    return [
        *PUBLIC_PILOT_PARTICIPANTS["drivers"],
        *PUBLIC_PILOT_PARTICIPANTS["riders"],
        *PUBLIC_PILOT_PARTICIPANTS["merchants"],
        *PUBLIC_PILOT_PARTICIPANTS["agents"],
        *PUBLIC_PILOT_PARTICIPANTS["businesses"],
        *PUBLIC_PILOT_PARTICIPANTS["employees"],
    ]


def _approved_device_ids() -> list[str]:
    return list(PUBLIC_PILOT_DEVICE_BINDINGS)


def _user_objects() -> list[dict[str, Any]]:
    objects: list[dict[str, Any]] = []
    singular = {
        "drivers": "driver",
        "riders": "rider",
        "merchants": "merchant",
        "agents": "agent",
        "businesses": "business",
        "employees": "employee",
    }
    for group_name, role in (
        ("drivers", "DRIVER"),
        ("riders", "CUSTOMER"),
        ("merchants", "CLIENT"),
        ("agents", "DISPATCHER"),
        ("businesses", "CLIENT"),
        ("employees", "EMPLOYEE"),
    ):
        for index, user_id in enumerate(PUBLIC_PILOT_PARTICIPANTS[group_name], start=1):
            objects.append(
                {
                    "user_id": user_id,
                    "group": singular[group_name],
                    "role": role,
                    "sequence": index,
                    "region": "Melbourne CBD" if group_name != "employees" else "Melbourne CBD",
                }
            )
    return objects


def _device_objects() -> list[dict[str, Any]]:
    return [
        {
            "device_id": device_id,
            "owner_id": owner_id,
            "trusted": True,
            "bound": True,
            "region": "Melbourne CBD",
        }
        for device_id, owner_id in PUBLIC_PILOT_DEVICE_BINDINGS.items()
    ]


def _group_objects(group_name: str, role: str) -> list[dict[str, Any]]:
    return [
        {
            "user_id": user_id,
            "group": group_name,
            "role": role,
            "region": "Melbourne CBD",
        }
        for user_id in PUBLIC_PILOT_PARTICIPANTS[group_name]
    ]


def public_pilot_approval_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "public_pilot_approved": True,
        "approval_id": "ppa-001",
        "approved_by": "public.pilot@novatech.test",
        "approved_at": "2026-07-08T00:00:00Z",
        "scope": "PUBLIC_PILOT_ONLY",
        "approved_regions": list(PUBLIC_PILOT_APPROVED_REGIONS),
        "approved_user_limit": 57,
        "limited_real_payments_approved": True,
        "real_identity_onboarding_approved": True,
        "real_ride_requests_approved": True,
        "public_pilot_live_payment_approved": False,
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
        "approved_users": _approved_user_ids(),
        "approved_devices": _approved_device_ids(),
        "approved_drivers": list(PUBLIC_PILOT_PARTICIPANTS["drivers"]),
        "approved_riders": list(PUBLIC_PILOT_PARTICIPANTS["riders"]),
        "approved_operators": [PUBLIC_PILOT_ACCOUNTS["operator"][0]],
        "approved_agents": list(PUBLIC_PILOT_PARTICIPANTS["agents"]),
        "approved_merchants": list(PUBLIC_PILOT_PARTICIPANTS["merchants"]),
        "approved_businesses": list(PUBLIC_PILOT_PARTICIPANTS["businesses"]),
        "approved_employees": list(PUBLIC_PILOT_PARTICIPANTS["employees"]),
    }
    payload.update(overrides)
    return payload


def public_pilot_population_payload() -> dict[str, Any]:
    return {
        "total_participants": 57,
        "groups": {
            "drivers": _group_objects("drivers", "DRIVER"),
            "riders": _group_objects("riders", "CUSTOMER"),
            "merchants": _group_objects("merchants", "CLIENT"),
            "agents": _group_objects("agents", "DISPATCHER"),
            "businesses": _group_objects("businesses", "CLIENT"),
            "employees": _group_objects("employees", "EMPLOYEE"),
        },
        "devices": _device_objects(),
        "approved_regions": list(PUBLIC_PILOT_APPROVED_LOCATIONS),
    }
