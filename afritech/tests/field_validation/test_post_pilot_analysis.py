from __future__ import annotations

import pytest

from afriride.field_validation.post_pilot_analysis import (
    ANALYSIS_BOUNDARY,
    NON_CLAIMS,
    REQUIRED_ANALYSIS_GATES,
    REQUIRED_DECISIONS,
    AnalysisGate,
    PostPilotAnalysisError,
    build_post_pilot_analysis_protocol,
    write_post_pilot_analysis_protocol,
)
from afritech.ci.afriride_post_pilot_analysis_validator import validate


def test_post_pilot_analysis_preserves_authority_boundary():
    payload = build_post_pilot_analysis_protocol().canonical_dict()

    assert payload["authority_boundary"] == ANALYSIS_BOUNDARY
    assert payload["decisions"] == list(REQUIRED_DECISIONS)
    assert payload["non_claims"] == list(NON_CLAIMS)
    assert "production_ready" in payload["non_claims"]
    assert "public_launch_ready" in payload["non_claims"]


def test_post_pilot_analysis_requires_all_gates():
    payload = build_post_pilot_analysis_protocol().canonical_dict()

    assert tuple(gate["name"] for gate in payload["gates"]) == REQUIRED_ANALYSIS_GATES
    assert "trace_manifest_complete" in REQUIRED_ANALYSIS_GATES
    assert "replay_equivalence_verified" in REQUIRED_ANALYSIS_GATES
    assert "non_claims_preserved" in REQUIRED_ANALYSIS_GATES


def test_post_pilot_analysis_separates_accept_defer_and_reject():
    payload = build_post_pilot_analysis_protocol().canonical_dict()
    actions = tuple(gate["failure_action"] for gate in payload["gates"])

    assert payload["allowed_pass_claim"].startswith("AfriRide pilot evidence is accepted")
    assert any(action.startswith("defer") for action in actions)
    assert any(action.startswith("reject") for action in actions)


def test_post_pilot_analysis_validator_accepts_protocol():
    report = validate()

    assert report.verified is True
    assert len(report.analysis_hash) == 64
    assert len(report.runbook_hash) == 64


def test_post_pilot_analysis_report_is_reproducible(tmp_path):
    output = tmp_path / "post_pilot_analysis.json"
    written = write_post_pilot_analysis_protocol(output)
    rebuilt = build_post_pilot_analysis_protocol()

    assert written.analysis_hash == rebuilt.analysis_hash


def test_post_pilot_analysis_rejects_unknown_gate():
    with pytest.raises(PostPilotAnalysisError):
        AnalysisGate(
            name="production_readiness_certified",
            pass_condition="pilot operator says ready",
            failure_action="accept production launch",
        )


def test_post_pilot_analysis_rejects_accepting_failure_action():
    with pytest.raises(PostPilotAnalysisError):
        AnalysisGate(
            name="trace_manifest_complete",
            pass_condition="all traces exist",
            failure_action="accept anyway",
        )
