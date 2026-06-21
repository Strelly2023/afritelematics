from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DEMO = ROOT / "docs/pitch/AFRIRIDE_INVESTOR_DEMO_VIDEO_PACKAGE.md"
NETWORK = ROOT / "docs/architecture/AFRIRIDE_MULTI_ORG_TRUST_NETWORK_ACTIVATION.md"
PILOT = ROOT / "docs/pilot/AFRIRIDE_MELBOURNE_FIRST_REAL_PILOT_LAUNCH_PLAN.md"


def test_investor_demo_video_package_is_truth_bounded() -> None:
    text = DEMO.read_text(encoding="utf-8")

    for required in (
        "INVESTOR-READY DEMO VIDEO PACKAGE",
        "ISOLATED INVESTOR COMMUNICATION SURFACE",
        "observable, replayable, trust-verifiable",
        "Verify this ride",
        "Download Verification Package",
        "GET /public/trust/{receipt_id}",
        "does not claim completed Melbourne",
    ):
        assert required in text


def test_multi_org_trust_network_activation_preserves_replay_authority() -> None:
    text = NETWORK.read_text(encoding="utf-8")

    for required in (
        "MULTI-ORG TRUST NETWORK ACTIVATION PLAN",
        "GOVERNED FEDERATION ACTIVATION SURFACE",
        "the trust network does not override replay authority",
        "POST /v1/trust/network/verify",
        "POST /v1/novascript/federation/trust-exchange",
        "Fleet Trust",
        "Compliance Reports",
        "No organization may claim replay authority.",
    ):
        assert required in text


def test_melbourne_first_real_pilot_launch_plan_has_execution_bounds() -> None:
    text = PILOT.read_text(encoding="utf-8")

    for required in (
        "READY-TO-RUN MELBOURNE PILOT LAUNCH PLAN",
        "FIELD EXECUTION PLANNING SURFACE",
        "Melbourne CBD <-> Melbourne Airport",
        "drivers: 3-5 trusted drivers",
        "trip_goal: 20-50 completed rides",
        "replay mismatch",
        "Melbourne pilot completed",
        "The pilot must not rely on investor narrative. The pilot must rely on evidence.",
    ):
        assert required in text
