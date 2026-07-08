from __future__ import annotations

from pathlib import Path

import pytest

from afriride_system.pilot.controlled_pilot import (
    ControlledPilotError,
    controlled_pilot_payment_allowed,
    controlled_pilot_payment_guard,
    mark_controlled_pilot_payment,
)
from tests.controlled_pilot._helpers import CONTROLLED_PILOT_CONFIG_PATH, read_json


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_payment_guard, pytest.mark.simulated_payment, pytest.mark.no_live_charge]


def test_payment_mode_is_simulated_and_live_paths_are_blocked() -> None:
    config = read_json("config/controlled_pilot.json")
    assert config["payment_mode"] == "SIMULATED_AND_SANDBOX"
    assert config["live_payments_enabled"] is False
    assert config["real_charging_enabled"] is False
    assert config["external_payouts_enabled"] is False

    assert controlled_pilot_payment_allowed() is False
    controlled_pilot_payment_guard(provider="wallet", method="wallet")
    controlled_pilot_payment_guard(provider="cash", method="cash")

    with pytest.raises(ControlledPilotError):
        controlled_pilot_payment_guard(provider="live_stripe", method="card")
    with pytest.raises(ControlledPilotError):
        controlled_pilot_payment_guard(provider="wallet", method="wallet", real_payment=True)
    with pytest.raises(ControlledPilotError):
        controlled_pilot_payment_guard(provider="wallet", method="wallet", production_credentials_present=True)
    with pytest.raises(ControlledPilotError):
        controlled_pilot_payment_guard(provider="wallet", method="unsupported")


def test_controlled_pilot_payment_payload_is_marked_simulated() -> None:
    payload = mark_controlled_pilot_payment({"transaction_id": "cp-001", "status": "captured"})
    assert payload["controlled_pilot"] is True
    assert payload["simulated_payment"] is True
    assert payload["payment_mode"] == "SIMULATED_AND_SANDBOX"
    assert payload["controlled_pilot_environment"]["environment"] == "CONTROLLED_PILOT"

    approval = Path("docs/pilot/PILOT_PAYMENT_APPROVAL.json")
    assert not approval.exists()
