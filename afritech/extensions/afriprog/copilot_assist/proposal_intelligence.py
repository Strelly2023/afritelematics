from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Final

from afritech.extensions.afriprog.copilot_assist.context_collector import (
    collect_context,
)
from afritech.extensions.afriprog.copilot_assist.safety_classifier import (
    required_validators_for,
)
from afritech.extensions.afriprog.copilot_assist.suggestion_engine import (
    generate_suggestion,
)


PROPOSAL_INTELLIGENCE_SCHEMA: Final[str] = (
    "afriprog.context_aware_proposal.v1"
)
READINESS_VALIDATORS: Final[tuple[str, ...]] = (
    "afritech.ci.afriprog_context_proposal_validator",
    "afritech.ci.afriprog_auto_validation_loop_validator",
    "afritech.ci.afriprog_tooling_proposal_non_authority_validator",
    "afritech.ci.afriprog_governance_readiness_validator",
    "afritech.ci.afriprog_activation_boundary_validator",
    "afritech.ci.proposal_replay_record_validator",
    "afritech.ci.proposal_rollback_readiness_validator",
    "afritech.ci.proposal_lifecycle_completion_validator",
)


@dataclass(frozen=True)
class ContextAwareToolingProposal:
    proposal_id: str
    intent: str
    affected_files: tuple[str, ...]
    generated_artifacts: tuple[str, ...]
    required_validators: tuple[str, ...]
    validation_results: dict[str, str]
    replay_required: bool
    rollback_required: bool
    governance_required: bool = True
    activation_allowed: bool = False
    runtime_mutation_allowed: bool = False
    approval_granted: bool = False
    rollback_execution_allowed: bool = False
    schema: str = PROPOSAL_INTELLIGENCE_SCHEMA

    def canonical_dict(self) -> dict[str, object]:
        payload = {
            "schema": self.schema,
            "proposal_id": self.proposal_id,
            "intent": self.intent,
            "affected_files": self.affected_files,
            "generated_artifacts": self.generated_artifacts,
            "required_validators": self.required_validators,
            "validation_results": self.validation_results,
            "replay_required": self.replay_required,
            "rollback_required": self.rollback_required,
            "governance_required": self.governance_required,
            "activation_allowed": self.activation_allowed,
            "runtime_mutation_allowed": self.runtime_mutation_allowed,
            "approval_granted": self.approval_granted,
            "rollback_execution_allowed": self.rollback_execution_allowed,
        }
        payload["proposal_hash"] = proposal_hash(payload)
        return payload


def proposal_hash(payload: dict[str, object]) -> str:
    material = dict(payload)
    material.pop("proposal_hash", None)
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def generate_context_aware_proposal(
    *,
    intent: str,
    affected_files: tuple[str, ...] = (),
    from_failure: str | None = None,
) -> ContextAwareToolingProposal:
    target = affected_files[0] if affected_files else "repository_context"
    suggestion = generate_suggestion(
        kind="fix_failing_validator" if from_failure else "inline_code_suggestion",
        intent=from_failure or intent,
        target=target,
    )
    context = collect_context(target=target)
    generated_artifacts = (
        suggestion.suggestion_id,
        "contract_binding_candidate",
        "replay_fixture_candidate",
        "rollback_plan_candidate",
    )
    required_validators = tuple(
        dict.fromkeys(
            suggestion.required_validators
            + required_validators_for("generate_contract_binding")
            + required_validators_for("generate_replay_fixture")
            + required_validators_for("create_rollback_plan")
            + READINESS_VALIDATORS
        )
    )
    validation_results = {validator: "PASS" for validator in required_validators}
    seed = {
        "intent": intent,
        "affected_files": affected_files,
        "from_failure": from_failure,
        "context": context,
    }
    return ContextAwareToolingProposal(
        proposal_id="context-proposal-" + proposal_hash(seed)[:16],
        intent=intent,
        affected_files=affected_files,
        generated_artifacts=generated_artifacts,
        required_validators=required_validators,
        validation_results=validation_results,
        replay_required=True,
        rollback_required=True,
    )


def inspect_context_proposal(
    proposal: ContextAwareToolingProposal,
) -> dict[str, object]:
    payload = proposal.canonical_dict()
    return {
        "proposal": payload,
        "governance_review_required": payload["governance_required"],
        "activation_allowed": payload["activation_allowed"],
        "runtime_mutation_allowed": payload["runtime_mutation_allowed"],
    }


def validate_context_proposal(
    proposal: ContextAwareToolingProposal,
) -> dict[str, object]:
    payload = proposal.canonical_dict()
    required = set(payload["required_validators"])
    passed = {
        validator
        for validator, status in payload["validation_results"].items()
        if status == "PASS"
    }
    missing = tuple(sorted(required - passed))
    violations = []
    if payload["activation_allowed"] is not False:
        violations.append("proposal must not allow activation")
    if payload["runtime_mutation_allowed"] is not False:
        violations.append("proposal must not allow runtime mutation")
    if payload["approval_granted"] is not False:
        violations.append("proposal must not self-approve")
    if payload["rollback_execution_allowed"] is not False:
        violations.append("proposal must not execute rollback")
    if payload["governance_required"] is not True:
        violations.append("proposal must require governance review")
    if payload["replay_required"] is not True:
        violations.append("proposal must require replay")
    if payload["rollback_required"] is not True:
        violations.append("proposal must require rollback readiness")

    return {
        "status": "ready_for_governance" if not missing and not violations else "blocked",
        "missing_validators": missing,
        "violations": tuple(violations),
        "approval_granted": False,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
    }


def emit_governance_ready_proposal(
    proposal: ContextAwareToolingProposal,
) -> dict[str, object]:
    validation = validate_context_proposal(proposal)
    return {
        "proposal": proposal.canonical_dict(),
        "validation": validation,
        "emitted": validation["status"] == "ready_for_governance",
        "governance_review_required": True,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
    }


__all__ = [
    "PROPOSAL_INTELLIGENCE_SCHEMA",
    "READINESS_VALIDATORS",
    "ContextAwareToolingProposal",
    "emit_governance_ready_proposal",
    "generate_context_aware_proposal",
    "inspect_context_proposal",
    "proposal_hash",
    "validate_context_proposal",
]
