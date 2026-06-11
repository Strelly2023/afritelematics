"""Non-authoritative AfriProgramming tooling helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from afritech.afriprogramming.tooling_manifest import (
    FINAL_AUTHORITIES,
    build_upgrade_classification,
    get_surface,
)


def build_cli_surface_catalog() -> dict[str, object]:
    surface = get_surface("afriprogramming_cli")
    return {
        "surface": surface.canonical_dict(),
        "commands": (
            "afri validate",
            "afri replay",
            "afri explain",
            "afri contract",
            "afri ai",
        ),
        "developer_tooling_only": True,
        "validators_remain_final": True,
    }


def build_ai_constraint_request(prompt: str) -> dict[str, object]:
    surface = get_surface("ai_constraint_engine")
    return {
        "surface": surface.surface_id,
        "prompt": prompt,
        "may_generate": True,
        "may_diagnose": True,
        "may_suggest_fixes": True,
        "accepted_without_validation": False,
        "final_authorities": FINAL_AUTHORITIES,
    }


def build_multi_agent_plan(objective: str) -> dict[str, object]:
    surface = get_surface("multi_agent_orchestrator")
    return {
        "surface": surface.surface_id,
        "objective": objective,
        "agents": ("generator", "diagnostician", "fix_suggester", "explainer"),
        "authority": "non_authoritative",
        "may_apply_changes": False,
        "must_submit_to_validators": True,
    }


def build_llm_envelope(prompt: str) -> dict[str, object]:
    surface = get_surface("llm_connector")
    return {
        "surface": surface.surface_id,
        "prompt": prompt,
        "network_call_performed": False,
        "model_output_trusted": False,
        "requires_validator_admission": True,
        "may_mutate_runtime": False,
    }


def build_vscode_view_model() -> dict[str, object]:
    surface = get_surface("vscode_extension")
    return {
        "surface": surface.surface_id,
        "ui_only": True,
        "invokes_cli": True,
        "defines_truth": False,
        "mutates_protected_runtime_state": False,
    }


def build_replay_graph(events: Iterable[Mapping[str, object]]) -> dict[str, object]:
    surface = get_surface("replay_graph_viewer")
    event_nodes = tuple(
        {
            "id": event.get("id"),
            "label": event.get("event_type") or event.get("name"),
            "status": event.get("status", "unknown"),
            "contract_receipt_hash": event.get("contract_receipt_hash"),
        }
        for event in events
    )
    return {
        "surface": surface.surface_id,
        "viewer_only": True,
        "nodes": event_nodes,
        "edges": tuple(
            {"from": event_nodes[index]["id"], "to": event_nodes[index + 1]["id"]}
            for index in range(max(len(event_nodes) - 1, 0))
        ),
        "replay_required_for_truth": True,
    }


def build_timeline_playback(events: Iterable[Mapping[str, object]]) -> dict[str, object]:
    surface = get_surface("timeline_playback_viewer")
    steps = tuple(
        {
            "step": index,
            "event_id": event.get("id"),
            "timestamp": event.get("timestamp"),
            "status": event.get("status", "unknown"),
            "explanation_available": True,
        }
        for index, event in enumerate(events)
    )
    return {
        "surface": surface.surface_id,
        "viewer_only": True,
        "steps": steps,
        "playback_defines_truth": False,
        "replay_required_for_truth": True,
    }


def explain_replay_step(step: Mapping[str, object]) -> dict[str, object]:
    return {
        "surface": "timeline_playback_viewer",
        "step": dict(step),
        "explanation_authority": "advisory",
        "defines_truth": False,
        "validators_remain_final": True,
    }


def build_governed_tooling_upgrade() -> dict[str, object]:
    classification = build_upgrade_classification()
    return {
        "classification": classification,
        "cli": build_cli_surface_catalog(),
        "ai_constraint_engine": build_ai_constraint_request("example"),
        "multi_agent_orchestrator": build_multi_agent_plan("example"),
        "llm_connector": build_llm_envelope("example"),
        "vscode_extension": build_vscode_view_model(),
        "replay_graph": build_replay_graph(()),
        "timeline_playback": build_timeline_playback(()),
    }


__all__ = [
    "build_ai_constraint_request",
    "build_cli_surface_catalog",
    "build_governed_tooling_upgrade",
    "build_llm_envelope",
    "build_multi_agent_plan",
    "build_replay_graph",
    "build_timeline_playback",
    "build_vscode_view_model",
    "explain_replay_step",
]
