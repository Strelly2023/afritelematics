from __future__ import annotations

import pytest

from tests.private_dev._helpers import read_json


pytestmark = [pytest.mark.private_dev, pytest.mark.local_only]


def test_private_development_configuration_is_locked_down() -> None:
    config = read_json("config/private_development.json")
    assert config["environment"] == "PRIVATE_DEVELOPMENT"
    assert config["live_payments_enabled"] is False
    assert config["real_charging_enabled"] is False
    assert config["external_payouts_enabled"] is False
    assert config["production_credentials_allowed"] is False
    assert config["public_launch_allowed"] is False
    assert config["controlled_pilot_allowed"] is False
    assert config["payment_mode"] == "SIMULATED"
    assert config["identity_mode"] == "SANDBOX"
    assert config["apk_distribution"] == "LOCAL_ONLY"

