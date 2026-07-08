from __future__ import annotations

import pytest

from tests.controlled_pilot._helpers import DOWNLOAD_PAGE_PATH, PILOT_REGISTRY_PATH, CONTROLLED_PILOT_CONFIG_PATH, read_json


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_release_guard]


def test_controlled_pilot_release_guard_blocks_public_ga_claims() -> None:
    config = read_json("config/controlled_pilot.json")
    registry = read_json("docs/pilot/approved_pilot_registry.json")
    assert config["environment"] == "CONTROLLED_PILOT"
    assert config["public_launch_allowed"] is False
    assert config["general_availability_allowed"] is False
    assert config["unrestricted_signup_allowed"] is False
    assert config["live_payments_enabled"] is False
    assert config["real_charging_enabled"] is False
    assert config["external_payouts_enabled"] is False
    assert registry["public_launch_allowed"] is False
    assert registry["real_payments_approved"] is False

    release_text = DOWNLOAD_PAGE_PATH.read_text(encoding="utf-8")
    assert "public launch" in release_text.lower()
    assert "general availability" in release_text.lower()
    assert "Controlled pilot only" in release_text


def test_controlled_pilot_payment_approval_file_is_absent_by_default() -> None:
    approval = PILOT_REGISTRY_PATH.parent / "PILOT_PAYMENT_APPROVAL.json"
    assert not approval.exists()
