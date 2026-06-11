"""Governed AfriProg to AfriProgramming handoff integration."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from afritech.afriprogramming.proposals import (
    ToolingProposal,
    emit_tooling_proposal,
    validate_proposal,
)
from afritech.extensions.afriprog.copilot_assist import (
    ContextAwareToolingProposal,
    emit_governance_ready_proposal,
    validate_context_proposal,
)


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class AfriProgBoundaryProfile:
    source_layer: str
    source_role: str
    source_question: str
    target_layer: str
    target_role: str
    target_question: str
    handoff_mode: str
    governance_required: bool
    replay_required: bool
    runtime_mutation_allowed: bool
    truth_authority_transferred: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "source_layer": self.source_layer,
            "source_role": self.source_role,
            "source_question": self.source_question,
            "target_layer": self.target_layer,
            "target_role": self.target_role,
            "target_question": self.target_question,
            "handoff_mode": self.handoff_mode,
            "governance_required": self.governance_required,
            "replay_required": self.replay_required,
            "runtime_mutation_allowed": self.runtime_mutation_allowed,
            "truth_authority_transferred": self.truth_authority_transferred,
        }


@dataclass(frozen=True)
class AfriProgIntegrationRecord:
    bridge_id: str
    boundary_profile: AfriProgBoundaryProfile
    source_proposal_id: str
    source_proposal_hash: str
    source_validation_status: str
    target_proposal_id: str
    target_proposal_hash: str
    target_validation_status: str
    governance_required: bool
    replay_required: bool
    activation_allowed: bool
    runtime_mutation_allowed: bool
    authority_boundary: str = "afriprog_feeds_afriprogramming_via_governed_proposals_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.afriprog_afriprogramming_integration.v1",
            "bridge_id": self.bridge_id,
            "boundary_profile": self.boundary_profile.canonical_dict(),
            "source_proposal_id": self.source_proposal_id,
            "source_proposal_hash": self.source_proposal_hash,
            "source_validation_status": self.source_validation_status,
            "target_proposal_id": self.target_proposal_id,
            "target_proposal_hash": self.target_proposal_hash,
            "target_validation_status": self.target_validation_status,
            "governance_required": self.governance_required,
            "replay_required": self.replay_required,
            "activation_allowed": self.activation_allowed,
            "runtime_mutation_allowed": self.runtime_mutation_allowed,
            "authority_boundary": self.authority_boundary,
        }


def build_afriprog_boundary_profile() -> AfriProgBoundaryProfile:
    return AfriProgBoundaryProfile(
        source_layer="AfriProg",
        source_role="productivity_and_repository_intelligence",
        source_question="What code should we write?",
        target_layer="AfriProgramming",
        target_role="governed_execution_and_evolution",
        target_question="Was this change allowed and can it be proven?",
        handoff_mode="proposal_only",
        governance_required=True,
        replay_required=True,
        runtime_mutation_allowed=False,
        truth_authority_transferred=False,
    )


def integrate_context_proposal(
    proposal: ContextAwareToolingProposal,
    *,
    origin_surface: str = "ai_constraint_engine",
    actor: str = "ai",
) -> AfriProgIntegrationRecord:
    inspected = emit_governance_ready_proposal(proposal)
    validation = validate_context_proposal(proposal)
    if validation["status"] != "ready_for_governance":
        raise RuntimeError("AfriProg proposal is not governance-ready for AfriProgramming")

    target = proposal.affected_files[0] if proposal.affected_files else "repository_context"
    bridging_payload = {
        "afriprog_proposal_id": proposal.proposal_id,
        "generated_artifacts": list(proposal.generated_artifacts),
        "required_validators": list(proposal.required_validators),
    }
    tooling_proposal = emit_tooling_proposal(
        origin=origin_surface,
        actor=actor,
        intent=proposal.intent,
        change_type="tooling_change",
        target=target,
        diff=json.dumps(bridging_payload, sort_keys=True, separators=(",", ":")),
    )
    validated_tooling = validate_proposal(tooling_proposal)
    source_payload = proposal.canonical_dict()
    target_payload = validated_tooling.canonical_dict()
    bridge_hash = _stable_hash(
        {
            "source_proposal_hash": source_payload["proposal_hash"],
            "target_proposal_hash": target_payload["proposal_hash"],
            "boundary_profile": build_afriprog_boundary_profile().canonical_dict(),
        }
    )
    return AfriProgIntegrationRecord(
        bridge_id=f"bridge-{bridge_hash[:16]}",
        boundary_profile=build_afriprog_boundary_profile(),
        source_proposal_id=proposal.proposal_id,
        source_proposal_hash=str(source_payload["proposal_hash"]),
        source_validation_status=str(validation["status"]),
        target_proposal_id=validated_tooling.proposal_id,
        target_proposal_hash=str(target_payload["proposal_hash"]),
        target_validation_status=validated_tooling.validation.status,
        governance_required=bool(inspected["governance_review_required"]),
        replay_required=bool(source_payload["replay_required"]),
        activation_allowed=bool(inspected["activation_allowed"]),
        runtime_mutation_allowed=bool(inspected["runtime_mutation_allowed"]),
    )


def build_afriprog_to_afriprogramming_view(
    proposal: ContextAwareToolingProposal,
) -> dict[str, Any]:
    integration = integrate_context_proposal(proposal)
    return {
        "boundary_profile": integration.boundary_profile.canonical_dict(),
        "integration_record": integration.canonical_dict(),
        "source_is_productivity_only": True,
        "target_is_governed_execution": True,
        "authority_boundary_preserved": not integration.boundary_profile.truth_authority_transferred,
    }


__all__ = [
    "AfriProgBoundaryProfile",
    "AfriProgIntegrationRecord",
    "build_afriprog_boundary_profile",
    "build_afriprog_to_afriprogramming_view",
    "integrate_context_proposal",
]
