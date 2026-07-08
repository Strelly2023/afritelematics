from __future__ import annotations

import pytest

from tests.controlled_pilot._helpers import CONTROLLED_PILOT_CONFIG_PATH, PILOT_REGISTRY_PATH, read_json


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_smoke]


def test_controlled_pilot_environment_is_locked_down() -> None:
    config = read_json("config/controlled_pilot.json")
    registry = read_json("docs/pilot/approved_pilot_registry.json")
    assert config["environment"] == "CONTROLLED_PILOT"
    assert config["pilot_enabled"] is True
    assert config["public_launch_allowed"] is False
    assert config["general_availability_allowed"] is False
    assert config["unrestricted_signup_allowed"] is False
    assert config["approved_users_only"] is True
    assert config["approved_devices_only"] is True
    assert config["approved_operators_only"] is True
    assert config["approved_participants_only"] is True
    assert config["roles_overlap_allowed"] is False
    assert config["payment_mode"] == "SIMULATED_AND_SANDBOX"
    assert config["live_payments_enabled"] is False
    assert config["real_charging_enabled"] is False
    assert config["external_payouts_enabled"] is False
    assert config["pilot_payment_approval_required"] is True
    assert config["apk_distribution"] == "CONTROLLED_ONLY"

    assert registry["pilot_id"] == "nova-controlled-pilot-001"
    assert registry["status"] == "CONTROLLED_PILOT"
    assert registry["approved_participants_only"] is True
    assert registry["roles_overlap_allowed"] is False
    assert registry["payment_mode"] == "SIMULATED_AND_SANDBOX"
    assert registry["real_payments_approved"] is False
    assert registry["public_launch_allowed"] is False
    assert len(registry["approved_users"]) == 57
    assert len(registry["approved_devices"]) == 40
