from __future__ import annotations

import pytest

from tests.internal_qa._helpers import INTERNAL_QA_CONFIG_PATH, read_json


pytestmark = [pytest.mark.internal_qa, pytest.mark.qa_smoke]


def test_internal_qa_configuration_is_locked_down() -> None:
    config = read_json(INTERNAL_QA_CONFIG_PATH)
    assert config["environment"] == "INTERNAL_QA"
    assert config["payment_mode"] == "SIMULATED"
    assert config["identity_mode"] == "SANDBOX"
    assert config["apk_distribution"] == "INTERNAL_ONLY"
    assert config["live_payments_enabled"] is False
    assert config["real_charging_enabled"] is False
    assert config["external_payouts_enabled"] is False
    assert config["production_credentials_allowed"] is False
    assert config["public_launch_allowed"] is False
    assert config["controlled_pilot_allowed"] is False
    assert config["internal_qa_enabled"] is True
