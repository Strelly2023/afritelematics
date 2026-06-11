from __future__ import annotations

import subprocess
import sys

from afritech.afriprogramming.tooling_manifest import (
    SURFACES,
    assert_tooling_boundaries,
    build_upgrade_classification,
)
from afritech.afriprogramming.tooling_surfaces import (
    build_ai_constraint_request,
    build_governed_tooling_upgrade,
    build_llm_envelope,
    build_multi_agent_plan,
    build_replay_graph,
    build_timeline_playback,
    build_vscode_view_model,
    explain_replay_step,
)
from afritech.ci import (
    afriprogramming_cli_surface_validator,
    ai_constraint_engine_validator,
    llm_boundary_validator,
    multi_agent_non_authority_validator,
    replay_graph_viewer_validator,
    timeline_playback_viewer_validator,
    vscode_extension_surface_validator,
)


VALIDATORS = (
    afriprogramming_cli_surface_validator,
    ai_constraint_engine_validator,
    multi_agent_non_authority_validator,
    llm_boundary_validator,
    vscode_extension_surface_validator,
    replay_graph_viewer_validator,
    timeline_playback_viewer_validator,
)


def test_tooling_manifest_preserves_authority_boundaries():
    assert_tooling_boundaries()
    classification = build_upgrade_classification()

    assert classification["afriprogramming_upgrade"] == "VALID_AS_TOOLING"
    assert classification["ai_authority"] == "NON_AUTHORITATIVE"
    assert classification["replay_authority"] == "PRESERVED"
    assert classification["governance_authority"] == "PRESERVED"
    assert classification["runtime_mutation_authority"] == "DENIED"
    assert classification["operational_claim"] == "NOT_EXPANDED"
    assert {surface.surface_id for surface in SURFACES} == {
        "afriprogramming_cli",
        "ai_constraint_engine",
        "multi_agent_orchestrator",
        "llm_connector",
        "vscode_extension",
        "replay_graph_viewer",
        "timeline_playback_viewer",
    }


def test_tooling_surfaces_are_non_authoritative():
    upgrade = build_governed_tooling_upgrade()
    ai_request = build_ai_constraint_request("driver endpoint")
    multi_agent = build_multi_agent_plan("fix replay failure")
    llm = build_llm_envelope("explain failure")
    vscode = build_vscode_view_model()
    graph = build_replay_graph(
        (
            {"id": "e1", "event_type": "RideRequested", "status": "valid"},
            {"id": "e2", "event_type": "RideAccepted", "status": "valid"},
        )
    )
    timeline = build_timeline_playback(
        (
            {
                "id": "e1",
                "timestamp": "2026-06-01T00:00:00Z",
                "status": "valid",
            },
        )
    )
    explanation = explain_replay_step(timeline["steps"][0])

    assert upgrade["classification"]["operational_claim"] == "NOT_EXPANDED"
    assert ai_request["accepted_without_validation"] is False
    assert multi_agent["may_apply_changes"] is False
    assert llm["model_output_trusted"] is False
    assert vscode["defines_truth"] is False
    assert graph["viewer_only"] is True
    assert timeline["playback_defines_truth"] is False
    assert explanation["explanation_authority"] == "advisory"


def test_requested_tooling_validators_pass_directly():
    afriprogramming_cli_surface_validator.validate_afriprogramming_cli_surface()
    ai_constraint_engine_validator.validate_ai_constraint_engine()
    multi_agent_non_authority_validator.validate_multi_agent_non_authority()
    llm_boundary_validator.validate_llm_boundary()
    vscode_extension_surface_validator.validate_vscode_extension_surface()
    replay_graph_viewer_validator.validate_replay_graph_viewer()
    timeline_playback_viewer_validator.validate_timeline_playback_viewer()


def test_requested_tooling_validator_cli_entrypoints_pass():
    for validator in VALIDATORS:
        result = subprocess.run(
            [sys.executable, "-m", validator.VALIDATOR_NAME],
            check=False,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASSED" in result.stdout
