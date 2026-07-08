from __future__ import annotations

import pytest

from afritech.guards.guard_activation_gate import validate as validate_activation_gates_guard
from tests.release._helpers import ACTIVATION_SOURCE, CONFIG_PATH, read_json, read_text


pytestmark = [pytest.mark.release, pytest.mark.activation_gate]


def test_activation_gate_configuration_has_expected_gates() -> None:
    config = read_json(CONFIG_PATH)
    gates = config["activationGates"]
    assert set(gates) == {
        "publicRegistration",
        "publicOnboarding",
        "realPayments",
        "countryActivation",
        "featureActivation",
        "merchantActivation",
        "agentActivation",
        "driverActivation",
    }
    assert gates["featureActivation"] is True
    assert gates["realPayments"] is False


def test_activation_gate_source_defines_required_gate_metadata() -> None:
    source = read_text(ACTIVATION_SOURCE)
    for phrase in ("PUBLIC_REGISTRATION", "REAL_PAYMENTS", "COUNTRY_ACTIVATION", "requiredStage", "requiredGuards", "requiredEvidence"):
        assert phrase in source


def test_activation_gate_guard_passes() -> None:
    report = validate_activation_gates_guard()
    assert report["status"] == "PASS"
    assert "featureActivation" in report["enabled_gates"]

