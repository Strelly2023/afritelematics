from __future__ import annotations

import pytest

from afriride.field_validation.live_pilot_protocol import (
    AUTHORITY_BOUNDARY,
    NON_CLAIMS,
    REQUIRED_OUTPUTS,
    REQUIRED_SCENARIOS,
    LivePilotProtocolError,
    PilotProtocol,
    PilotScale,
    build_live_pilot_protocol,
    write_live_pilot_protocol,
)
from afritech.ci.afriride_live_pilot_protocol_validator import validate


def test_live_pilot_protocol_defines_exact_controlled_scale():
    protocol = build_live_pilot_protocol()
    payload = protocol.canonical_dict()

    assert payload["scale"]["drivers_min"] == 5
    assert payload["scale"]["drivers_max"] == 20
    assert payload["scale"]["riders_min"] == 10
    assert payload["scale"]["riders_max"] == 60
    assert payload["authority_boundary"] == AUTHORITY_BOUNDARY


def test_live_pilot_protocol_covers_roles_devices_scripts_and_outputs():
    payload = build_live_pilot_protocol().canonical_dict()

    assert tuple(script["scenario"] for script in payload["scenario_scripts"]) == REQUIRED_SCENARIOS
    assert tuple(payload["evidence_outputs"]) == REQUIRED_OUTPUTS
    assert {role["role"] for role in payload["operator_roles"]} == {
        "pilot_controller",
        "proof_operator",
        "support_operator",
        "safety_observer",
    }
    assert payload["device_plan"]["driver_devices"]["count"] == "5-20"
    assert "pilot_trace_manifest.json" in payload["evidence_outputs"]


def test_live_pilot_protocol_preserves_claim_boundary():
    payload = build_live_pilot_protocol().canonical_dict()

    assert tuple(payload["claim_boundary"]["non_claims"]) == NON_CLAIMS
    assert "completed_real_world_pilot" in payload["claim_boundary"]["non_claims"]
    assert "manual truth override attempted" in payload["stop_conditions"]
    assert "pilot scope escape" in payload["stop_conditions"]


def test_live_pilot_protocol_validator_accepts_protocol():
    report = validate()

    assert report.verified is True
    assert len(report.protocol_hash) == 64


def test_live_pilot_protocol_report_is_reproducible(tmp_path):
    output = tmp_path / "live_pilot_protocol.json"
    written = write_live_pilot_protocol(output)
    rebuilt = build_live_pilot_protocol()

    assert written.protocol_hash == rebuilt.protocol_hash


def test_live_pilot_protocol_rejects_out_of_scope_driver_count():
    with pytest.raises(LivePilotProtocolError):
        PilotProtocol(scale=PilotScale(drivers_min=5, drivers_max=21))
