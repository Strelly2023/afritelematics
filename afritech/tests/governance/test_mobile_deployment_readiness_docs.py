from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RELEASE = ROOT / "docs/mobile/AFRIRIDE_APP_STORE_AND_PLAY_STORE_RELEASE_CHECKLIST.md"
OFFLINE = ROOT / "docs/mobile/AFRIRIDE_OFFLINE_FIRST_EVENT_QUEUE_SPEC.md"
DEVICE = ROOT / "docs/mobile/AFRIRIDE_DEVICE_CERTIFICATION_TEST_PLAN.md"
UX = ROOT / "docs/mobile/AFRIRIDE_MOBILE_UX_POLISH_GUIDE.md"


def test_release_checklist_covers_expo_distribution_and_endpoint_discipline() -> None:
    text = RELEASE.read_text(encoding="utf-8")
    for item in (
        "APP STORE AND PLAY STORE RELEASE CHECKLIST",
        "expo start --android",
        "expo start --ios",
        "EXPO_PUBLIC_AFRIRIDE_API_URL",
        "10.0.2.2",
        "TestFlight",
        "Play internal testing",
    ):
        assert item in text


def test_offline_first_spec_requires_queue_order_and_idempotency_reuse() -> None:
    text = OFFLINE.read_text(encoding="utf-8")
    for item in (
        "OFFLINE-FIRST EVENT QUEUE SPECIFICATION",
        "Queue Before Lossy Retry",
        "logical clock order first",
        "Idempotent Replay Safety",
        "same idempotency key across retry attempts",
        "No Local Truth Override",
    ):
        assert item in text


def test_device_certification_plan_covers_real_device_and_weak_network_checks() -> None:
    text = DEVICE.read_text(encoding="utf-8")
    for item in (
        "DEVICE CERTIFICATION TEST PLAN",
        "physical Android phone",
        "iOS simulator or iPhone",
        "airplane-mode interruption rehearsal",
        "receipt fetch succeeds",
        "no duplicate committed action appears from retry behavior",
    ):
        assert item in text


def test_mobile_ux_polish_guide_preserves_authority_boundary() -> None:
    text = UX.read_text(encoding="utf-8")
    for item in (
        "MOBILE UX POLISH GUIDE",
        "Rider Priorities",
        "Driver Priorities",
        "Operator Priorities",
        "UX polish may not redefine truth",
    ):
        assert item in text
