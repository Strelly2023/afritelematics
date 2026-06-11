"""Governed AfriProgramming tooling surface manifest.

This module admits the AfriProgramming upgrade as developer tooling only.
It deliberately does not provide runtime, proof, replay, governance, or
constitutional authority to AI, IDE, dashboard, or visualization surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


FINAL_AUTHORITIES: Final[tuple[str, ...]] = (
    "contracts",
    "validators",
    "replay",
    "constitutional_governance",
)

ALLOWED_AI_ACTIONS: Final[tuple[str, ...]] = (
    "generate",
    "diagnose",
    "suggest_fixes",
    "explain",
)

FORBIDDEN_SURFACE_ACTIONS: Final[tuple[str, ...]] = (
    "define_truth",
    "bypass_validators",
    "mutate_protected_runtime_state",
    "mutate_governance_state",
    "mutate_proof_state",
    "mutate_replay_state",
    "emit_constitutional_attestation",
    "emit_witness",
    "claim_production_readiness",
    "expand_operational_claims",
)


@dataclass(frozen=True)
class AfriProgrammingSurface:
    """A non-authoritative developer tooling surface."""

    surface_id: str
    label: str
    role: str
    status: str
    authority: str
    allowed_actions: tuple[str, ...]
    required_validator: str
    requires_validator_gate: bool = True
    requires_replay_gate: bool = True
    may_define_truth: bool = False
    may_bypass_validators: bool = False
    may_mutate_protected_runtime_state: bool = False
    may_emit_proof: bool = False
    may_emit_witness: bool = False
    may_attest_constitutionally: bool = False
    expands_operational_claims: bool = False

    def canonical_dict(self) -> dict[str, object]:
        return {
            "surface_id": self.surface_id,
            "label": self.label,
            "role": self.role,
            "status": self.status,
            "authority": self.authority,
            "allowed_actions": self.allowed_actions,
            "required_validator": self.required_validator,
            "requires_validator_gate": self.requires_validator_gate,
            "requires_replay_gate": self.requires_replay_gate,
            "may_define_truth": self.may_define_truth,
            "may_bypass_validators": self.may_bypass_validators,
            "may_mutate_protected_runtime_state": (
                self.may_mutate_protected_runtime_state
            ),
            "may_emit_proof": self.may_emit_proof,
            "may_emit_witness": self.may_emit_witness,
            "may_attest_constitutionally": self.may_attest_constitutionally,
            "expands_operational_claims": self.expands_operational_claims,
        }


SURFACES: Final[tuple[AfriProgrammingSurface, ...]] = (
    AfriProgrammingSurface(
        surface_id="afriprogramming_cli",
        label="AfriProgramming CLI",
        role="developer_tooling",
        status="valid_as_tooling",
        authority="non_authoritative",
        allowed_actions=("inspect", "validate", "replay", "explain", "delegate"),
        required_validator="afritech.ci.afriprogramming_cli_surface_validator",
    ),
    AfriProgrammingSurface(
        surface_id="ai_constraint_engine",
        label="AI Constraint Engine",
        role="advisory_generation_layer",
        status="valid_as_tooling",
        authority="non_authoritative",
        allowed_actions=ALLOWED_AI_ACTIONS,
        required_validator="afritech.ci.ai_constraint_engine_validator",
    ),
    AfriProgrammingSurface(
        surface_id="multi_agent_orchestrator",
        label="Multi-Agent Orchestrator",
        role="non_authoritative_coordination",
        status="valid_as_tooling",
        authority="non_authoritative",
        allowed_actions=("plan", "diagnose", "suggest_fixes", "explain"),
        required_validator="afritech.ci.multi_agent_non_authority_validator",
    ),
    AfriProgrammingSurface(
        surface_id="llm_connector",
        label="LLM Connector",
        role="validator_gated_model_adapter",
        status="valid_as_tooling",
        authority="non_authoritative",
        allowed_actions=("request_suggestion", "request_diagnosis", "request_explanation"),
        required_validator="afritech.ci.llm_boundary_validator",
    ),
    AfriProgrammingSurface(
        surface_id="vscode_extension",
        label="VSCode Extension",
        role="ui_only",
        status="valid_as_tooling",
        authority="non_authoritative",
        allowed_actions=("display", "invoke_cli", "show_diagnostics", "show_explanations"),
        required_validator="afritech.ci.vscode_extension_surface_validator",
    ),
    AfriProgrammingSurface(
        surface_id="replay_graph_viewer",
        label="Replay Graph Viewer",
        role="visualization_only",
        status="valid_as_tooling",
        authority="non_authoritative",
        allowed_actions=("render_graph", "display_contract_bindings", "explain"),
        required_validator="afritech.ci.replay_graph_viewer_validator",
    ),
    AfriProgrammingSurface(
        surface_id="timeline_playback_viewer",
        label="Timeline Playback Viewer",
        role="replay_viewer_only",
        status="valid_as_tooling",
        authority="non_authoritative",
        allowed_actions=("render_timeline", "playback", "explain_step"),
        required_validator="afritech.ci.timeline_playback_viewer_validator",
    ),
)


def get_surface(surface_id: str) -> AfriProgrammingSurface:
    for surface in SURFACES:
        if surface.surface_id == surface_id:
            return surface
    raise KeyError(f"unknown AfriProgramming tooling surface: {surface_id}")


def build_upgrade_classification() -> dict[str, object]:
    return {
        "afriprogramming_upgrade": "VALID_AS_TOOLING",
        "ai_authority": "NON_AUTHORITATIVE",
        "replay_authority": "PRESERVED",
        "governance_authority": "PRESERVED",
        "runtime_mutation_authority": "DENIED",
        "operational_claim": "NOT_EXPANDED",
        "violation_status": "NO_VIOLATION_IF_VALIDATORS_PASS",
        "final_authorities": FINAL_AUTHORITIES,
        "forbidden_surface_actions": FORBIDDEN_SURFACE_ACTIONS,
        "surfaces": tuple(surface.canonical_dict() for surface in SURFACES),
    }


def assert_tooling_boundaries() -> None:
    seen: set[str] = set()
    for surface in SURFACES:
        if surface.surface_id in seen:
            raise RuntimeError(f"duplicate tooling surface: {surface.surface_id}")
        seen.add(surface.surface_id)

        if surface.authority != "non_authoritative":
            raise RuntimeError(f"{surface.surface_id} gained authority")
        if surface.status != "valid_as_tooling":
            raise RuntimeError(f"{surface.surface_id} is not tooling-scoped")
        if not surface.requires_validator_gate:
            raise RuntimeError(f"{surface.surface_id} may bypass validators")
        if not surface.requires_replay_gate:
            raise RuntimeError(f"{surface.surface_id} bypasses replay")
        if surface.may_define_truth:
            raise RuntimeError(f"{surface.surface_id} may define truth")
        if surface.may_bypass_validators:
            raise RuntimeError(f"{surface.surface_id} may bypass validators")
        if surface.may_mutate_protected_runtime_state:
            raise RuntimeError(f"{surface.surface_id} may mutate runtime")
        if surface.may_emit_proof or surface.may_emit_witness:
            raise RuntimeError(f"{surface.surface_id} may emit proof or witness")
        if surface.may_attest_constitutionally:
            raise RuntimeError(f"{surface.surface_id} may attest constitutionally")
        if surface.expands_operational_claims:
            raise RuntimeError(f"{surface.surface_id} expands operational claims")


__all__ = [
    "ALLOWED_AI_ACTIONS",
    "FINAL_AUTHORITIES",
    "FORBIDDEN_SURFACE_ACTIONS",
    "SURFACES",
    "AfriProgrammingSurface",
    "assert_tooling_boundaries",
    "build_upgrade_classification",
    "get_surface",
]
