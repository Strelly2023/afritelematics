from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_FILES = (
    "docs/mobile/afriride_app_store_master_plan.md",
    "docs/mobile/store_listing_content.md",
    "docs/mobile/legal/privacy_policy_template.md",
    "docs/mobile/legal/terms_of_service_template.md",
    "docs/mobile/legal/support_page_template.md",
    "docs/mobile/release/afriride_mobile_release_readiness.json",
    "docs/mobile/release/rider_app_release_manifest.json",
    "docs/mobile/release/driver_app_release_manifest.json",
    "docs/mobile/release/operator_dashboard_release_manifest.json",
    "docs/api/afriride_mobile_api_contract.md",
    "docs/pilot/AFRIRIDE_PILOT_ACTIVATION_CHECKLIST.md",
    "afriride_system/flutter/driver_app/pubspec.yaml",
    "afriride_system/flutter/rider_app/pubspec.yaml",
)

REQUIRED_TEXT = (
    (
        "docs/mobile/afriride_app_store_master_plan.md",
        "AfriRide uses a replay-governed execution model",
    ),
    (
        "docs/mobile/afriride_app_store_master_plan.md",
        "Live public production claims may not",
    ),
    (
        "docs/mobile/store_listing_content.md",
        "Do Not Claim",
    ),
    (
        "docs/api/afriride_mobile_api_contract.md",
        "Mobile apps are interface-only",
    ),
    (
        "docs/mobile/release/afriride_mobile_release_readiness.json",
        "PILOT_RELEASE_READY_STORE_PRODUCTION_BLOCKED",
    ),
    (
        "docs/mobile/release/rider_app_release_manifest.json",
        "afriride-rider",
    ),
    (
        "docs/mobile/release/driver_app_release_manifest.json",
        "afriride-driver",
    ),
    (
        "docs/mobile/release/operator_dashboard_release_manifest.json",
        "afriride-operator-dashboard",
    ),
    (
        "docs/pilot/AFRIRIDE_PILOT_ACTIVATION_CHECKLIST.md",
        "go_authorized = false",
    ),
)


def validate() -> bool:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing:
        raise SystemExit(f"missing app-store deployment files: {missing}")

    for path, needle in REQUIRED_TEXT:
        text = (ROOT / path).read_text(encoding="utf-8")
        if needle not in text:
            raise SystemExit(f"missing required text in {path}: {needle}")

    return True


def main() -> int:
    validate()
    print("AFRIRIDE_APP_STORE_DEPLOYMENT_VALIDATOR: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
