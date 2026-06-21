from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
API = ROOT / "docs/api/AFRIRIDE_NEXT_GEN_MOBILE_API_CONTRACT.md"
WIREFRAMES = ROOT / "docs/mobile/AFRIRIDE_NEXT_GEN_UI_WIREFRAMES.md"
BUILD = ROOT / "docs/mobile/AFRIRIDE_REACT_NATIVE_APP_STORE_BUILD_PLAN.md"


def test_next_gen_mobile_api_contract_covers_trust_native_rider_and_driver_endpoints() -> None:
    text = API.read_text(encoding="utf-8")

    for required in (
        "NEXT-GEN RIDER AND DRIVER API CONTRACT",
        "Mobile apps must never finalize receipts",
        "POST /v1/rider/rides",
        "GET /v1/rider/rides/{ride_id}/receipt",
        "GET /v1/rider/rides/{ride_id}/replay",
        "GET /v1/driver/{driver_id}/ride-queue",
        "POST /v1/driver/rides/{ride_id}/complete",
        "GET /v1/operator/dashboard",
        "Replay Exceptions",
        "Public Verification Status",
        "GET /public/trust/{receipt_id}",
        "GET /public/trust/{receipt_id}/package",
        "state_transition_rejected",
    ):
        assert required in text


def test_next_gen_wireframes_define_figma_level_rider_driver_surfaces() -> None:
    text = WIREFRAMES.read_text(encoding="utf-8")

    for required in (
        "FIGMA-LEVEL MOBILE WIREFRAME SPEC",
        "Rider / 01 Booking",
        "Rider / 04 Receipt",
        "Driver / 01 Availability",
        "Driver / 03 Trip Lifecycle",
        "TrustBadge",
        "LifecycleRail",
        "Verify this ride",
        "Download Verification Package",
        "The app displays proof results; it does not create proof authority.",
    ):
        assert required in text


def test_react_native_app_store_build_plan_is_pilot_gated() -> None:
    text = BUILD.read_text(encoding="utf-8")

    for required in (
        "APP STORE READY BUILD PLAN",
        "rider_app  -> AfriRide Rider",
        "driver_app -> AfriRide Driver",
        "npm run typecheck",
        "pytest -q rider_app/tests driver_app/tests",
        "EXPO_PUBLIC_AFRIRIDE_API_URL",
        "TestFlight",
        "Google Play internal testing",
        "App Store Submission Assets",
        "pilot reviewer notes with test rider and driver credentials",
        "demo receipt ID for public verification review",
        "Do not submit if any condition exists",
        "AfriRide is already approved for public production release.",
    ):
        assert required in text
