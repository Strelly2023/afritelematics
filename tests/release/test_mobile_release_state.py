from __future__ import annotations

import pytest

from tests.release._helpers import MOBILE_STATE_PATH, read_json


pytestmark = [pytest.mark.release]


def test_mobile_release_state_exposes_release_stage_and_gates() -> None:
    state = read_json(MOBILE_STATE_PATH)
    assert state["release_stage"] == "PUBLIC_PILOT"
    assert state["activation_gates"]["featureActivation"] is True
    assert state["activation_gates"]["realPayments"] is False
    assert state["readiness_status"]["Governance"] == "PASS"

