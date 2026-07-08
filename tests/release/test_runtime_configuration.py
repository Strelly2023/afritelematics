from __future__ import annotations

import pytest

from tests.release._helpers import CONFIG_PATH, MOBILE_STATE_PATH, read_json, read_text


pytestmark = [pytest.mark.release]


def test_runtime_configuration_contains_machine_enforceable_state() -> None:
    config = read_json(CONFIG_PATH)
    assert config["environment"] == "PUBLIC_PILOT"
    assert config["pilotMonitoringRequired"] is True
    assert config["incidentResponseRequired"] is True
    assert config["rollbackRequired"] is True
    assert config["supportRequired"] is True
    assert config["productionCredentialsAllowed"] is True
    assert config["publicUsersAllowed"] is True


def test_mobile_release_state_doc_exists() -> None:
    state = read_json(MOBILE_STATE_PATH)
    assert state["release_stage"] == "PUBLIC_PILOT"
    assert state["pilot_status"] == "READY_FOR_PRR"
    assert state["payment_mode"] == "PILOT_REAL_LIMITED"
    assert state["trust_status"] == "ENABLED"


def test_mobile_release_state_is_consumable_by_dashboards_and_apps() -> None:
    text = read_text(MOBILE_STATE_PATH)
    for phrase in ("release_stage", "activation_gates", "readiness_status", "pilot_status"):
        assert phrase in text

