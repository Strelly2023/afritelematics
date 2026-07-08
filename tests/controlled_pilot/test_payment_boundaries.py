from __future__ import annotations

import pytest

from afriride_system.pilot.controlled_pilot import ControlledPilotError, controlled_pilot_payment_guard
from tests.controlled_pilot._helpers import read_json


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_payment_guard, pytest.mark.simulated_payment, pytest.mark.no_live_charge]


def test_controlled_pilot_payment_boundaries_are_enforced() -> None:
    config = read_json("config/controlled_pilot.json")
    assert config["payment_mode"] == "SIMULATED_AND_SANDBOX"
    assert config["live_payments_enabled"] is False
    assert config["real_charging_enabled"] is False
    assert config["external_payouts_enabled"] is False

    controlled_pilot_payment_guard(provider="wallet", method="wallet")
    controlled_pilot_payment_guard(provider="cash", method="cash")

    with pytest.raises(ControlledPilotError):
        controlled_pilot_payment_guard(provider="live_stripe", method="card")
    with pytest.raises(ControlledPilotError):
        controlled_pilot_payment_guard(provider="wallet", method="wallet", real_payment=True)
    with pytest.raises(ControlledPilotError):
        controlled_pilot_payment_guard(provider="wallet", method="wallet", payout=True)
    with pytest.raises(ControlledPilotError):
        controlled_pilot_payment_guard(provider="wallet", method="wallet", production_credentials_present=True)

