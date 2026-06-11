"""Governed proposal flow for AfriProgramming tooling.

Tooling may express mutation intent only as a proposal artifact. Validation,
explicit governance approval, and activation gating are required before any
state transition can be considered ready for a runtime activation layer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Final

from afritech.afriprogramming.tooling_manifest import get_surface


PROPOSAL_SCHEMA: Final[str] = "afriprogramming.tooling_proposal.v1"
VALIDATION_STATUSES: Final[tuple[str, ...]] = ("pending", "pass", "fail")
GOVERNANCE_STATUSES: Final[tuple[str, ...]] = ("pending", "approved", "rejected")
ACTIVATION_STATUSES: Final[tuple[str, ...]] = ("blocked", "ready")
LIFECYCLE_STATUSES: Final[tuple[str, ...]] = (
    "activated",
    "recorded",
    "replayable",
    "rollback_ready",
    "complete",
)
ALLOWED_ACTORS: Final[tuple[str, ...]] = ("ai", "user", "system")
ALLOWED_CHANGE_TYPES: Final[tuple[str, ...]] = (
    "contract_update",
    "config_change",
    "tooling_change",
    "validator_change",
    "documentation_change",
)
PROTECTED_TARGET_PREFIXES: Final[tuple[str, ...]] = (
    "afritech/governance/",
    "afritech/proof/",
    "afritech/runtime/",
    "afritech/registry/",
    "afritech/models/trust_kernel.py",
    "afritech/ci/constitutional_validation.py",
)


class ToolingProposalError(RuntimeError):
    """Raised when a proposal violates the governed mutation pipeline."""


@dataclass(frozen=True)
class ChangeSet:
    change_type: str
    target: str
    diff: str

    def canonical_dict(self) -> dict[str, str]:
        return {
            "type": self.change_type,
            "target": self.target,
            "diff": self.diff,
        }


@dataclass(frozen=True)
class ProposalValidation:
    status: str = "pending"
    validators: tuple[str, ...] = ()
    violations: tuple[str, ...] = ()

    def canonical_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "validators": self.validators,
            "violations": self.violations,
        }


@dataclass(frozen=True)
class GovernanceApproval:
    status: str = "pending"
    approved_by: tuple[str, ...] = ()
    timestamp: str | None = None
    approval_ref: str | None = None

    def canonical_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "approved_by": self.approved_by,
            "timestamp": self.timestamp,
            "approval_ref": self.approval_ref,
        }


@dataclass(frozen=True)
class ActivationState:
    status: str = "blocked"
    timestamp: str | None = None
    execution_performed: bool = False

    def canonical_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "timestamp": self.timestamp,
            "execution_performed": self.execution_performed,
        }


@dataclass(frozen=True)
class ActivationRecord:
    proposal_id: str
    timestamp: str
    pre_state: dict[str, object]
    post_state: dict[str, object]
    applied_diff: tuple[dict[str, object], ...]
    replay_hash: str
    validator_status: str
    governance_reference: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp,
            "pre_state": self.pre_state,
            "post_state": self.post_state,
            "applied_diff": self.applied_diff,
            "replay_hash": self.replay_hash,
            "validator_status": self.validator_status,
            "governance_reference": self.governance_reference,
        }


@dataclass(frozen=True)
class RollbackPlan:
    proposal_id: str
    rollback_diff: tuple[dict[str, object], ...]
    target_state: dict[str, object]
    constraints: tuple[str, ...]
    governance_required: bool = True
    validated: bool = False

    def canonical_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "rollback_diff": self.rollback_diff,
            "target_state": self.target_state,
            "constraints": self.constraints,
            "governance_required": self.governance_required,
            "validated": self.validated,
        }


@dataclass(frozen=True)
class ProposalLifecycle:
    proposal_id: str
    status: str
    activation_record: ActivationRecord
    rollback_plan: RollbackPlan
    replay_proven: bool
    rollback_validated: bool
    rollback_execution_performed: bool = False

    def canonical_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "status": self.status,
            "activation_record": self.activation_record.canonical_dict(),
            "rollback_plan": self.rollback_plan.canonical_dict(),
            "replay_proven": self.replay_proven,
            "rollback_validated": self.rollback_validated,
            "rollback_execution_performed": self.rollback_execution_performed,
        }


@dataclass(frozen=True)
class ToolingProposal:
    proposal_id: str
    origin: str
    actor: str
    intent: str
    change_set: ChangeSet
    validation: ProposalValidation = ProposalValidation()
    governance: GovernanceApproval = GovernanceApproval()
    activation: ActivationState = ActivationState()
    schema: str = PROPOSAL_SCHEMA

    def canonical_dict(self) -> dict[str, object]:
        payload = {
            "schema": self.schema,
            "id": self.proposal_id,
            "origin": self.origin,
            "actor": self.actor,
            "intent": self.intent,
            "change_set": self.change_set.canonical_dict(),
            "validation": self.validation.canonical_dict(),
            "governance": self.governance.canonical_dict(),
            "activation": self.activation.canonical_dict(),
        }
        payload["proposal_hash"] = proposal_hash(payload, include_hash=False)
        return payload


def proposal_hash(payload: dict[str, object], include_hash: bool = True) -> str:
    material = dict(payload)
    if not include_hash:
        material.pop("proposal_hash", None)
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def emit_tooling_proposal(
    *,
    origin: str,
    actor: str,
    intent: str,
    change_type: str,
    target: str,
    diff: str,
) -> ToolingProposal:
    get_surface(origin)
    change_set = ChangeSet(change_type=change_type, target=target, diff=diff)
    seed = {
        "schema": PROPOSAL_SCHEMA,
        "origin": origin,
        "actor": actor,
        "intent": intent,
        "change_set": change_set.canonical_dict(),
    }
    proposal_id = "tooling-proposal-" + proposal_hash(seed, include_hash=False)[:16]
    return ToolingProposal(
        proposal_id=proposal_id,
        origin=origin,
        actor=actor,
        intent=intent,
        change_set=change_set,
    )


def validate_proposal(proposal: ToolingProposal) -> ToolingProposal:
    violations = tuple(_proposal_violations(proposal))
    status = "fail" if violations else "pass"
    validation = ProposalValidation(
        status=status,
        validators=("afritech.ci.tooling_proposal_emission_validator",),
        violations=violations,
    )
    return replace(proposal, validation=validation)


def approve_proposal(
    proposal: ToolingProposal,
    *,
    approved_by: tuple[str, ...],
    timestamp: str,
    approval_ref: str,
) -> ToolingProposal:
    if proposal.validation.status != "pass":
        raise ToolingProposalError("proposal must pass validation before approval")
    if not approved_by:
        raise ToolingProposalError("governance approval must be explicit")
    governance = GovernanceApproval(
        status="approved",
        approved_by=approved_by,
        timestamp=timestamp,
        approval_ref=approval_ref,
    )
    return replace(proposal, governance=governance)


def reject_proposal(
    proposal: ToolingProposal,
    *,
    approval_ref: str,
) -> ToolingProposal:
    governance = GovernanceApproval(status="rejected", approval_ref=approval_ref)
    return replace(proposal, governance=governance)


def activation_gate(
    proposal: ToolingProposal,
    *,
    timestamp: str,
) -> ToolingProposal:
    if proposal.validation.status != "pass":
        raise ToolingProposalError("activation blocked: proposal validation missing")
    if proposal.governance.status != "approved":
        raise ToolingProposalError("activation blocked: governance approval missing")
    if not proposal.governance.approved_by:
        raise ToolingProposalError("activation blocked: approval signer missing")

    activation = ActivationState(
        status="ready",
        timestamp=timestamp,
        execution_performed=False,
    )
    return replace(proposal, activation=activation)


def build_activation_record(
    proposal: ToolingProposal,
    *,
    pre_state: dict[str, object],
    post_state: dict[str, object],
    applied_diff: tuple[dict[str, object], ...],
    timestamp: str,
    validator_status: str = "PASS",
) -> ActivationRecord:
    if proposal.activation.status != "ready":
        raise ToolingProposalError("activation record requires activation-ready proposal")
    if validator_status != "PASS":
        raise ToolingProposalError("activation record requires passing validators")
    if not proposal.governance.approval_ref:
        raise ToolingProposalError("activation record requires governance reference")

    reconstructed = apply_diff(pre_state, applied_diff)
    if reconstructed != post_state:
        raise ToolingProposalError("activation diff does not replay to post-state")

    replay_payload = {
        "proposal_id": proposal.proposal_id,
        "pre_state": pre_state,
        "post_state": post_state,
        "applied_diff": applied_diff,
        "governance_reference": proposal.governance.approval_ref,
    }
    return ActivationRecord(
        proposal_id=proposal.proposal_id,
        timestamp=timestamp,
        pre_state=pre_state,
        post_state=post_state,
        applied_diff=applied_diff,
        replay_hash=proposal_hash(replay_payload, include_hash=False),
        validator_status=validator_status,
        governance_reference=proposal.governance.approval_ref,
    )


def replay_activation_record(record: ActivationRecord) -> bool:
    return apply_diff(record.pre_state, record.applied_diff) == record.post_state


def build_rollback_plan(record: ActivationRecord) -> RollbackPlan:
    rollback_diff = invert_diff(record.applied_diff, record.pre_state)
    return RollbackPlan(
        proposal_id=record.proposal_id,
        rollback_diff=rollback_diff,
        target_state=record.pre_state,
        constraints=(
            "must_preserve_replay_correctness",
            "must_not_violate_contract_timeline",
            "must_require_governance_approval",
        ),
    )


def validate_rollback_plan(
    record: ActivationRecord,
    plan: RollbackPlan,
) -> RollbackPlan:
    if plan.proposal_id != record.proposal_id:
        raise ToolingProposalError("rollback plan proposal mismatch")
    if plan.governance_required is not True:
        raise ToolingProposalError("rollback execution must require governance")
    if not plan.rollback_diff:
        raise ToolingProposalError("rollback diff is required")
    if apply_diff(record.post_state, plan.rollback_diff) != plan.target_state:
        raise ToolingProposalError("rollback diff does not replay to target state")
    return replace(plan, validated=True)


def complete_proposal_lifecycle(
    record: ActivationRecord,
    plan: RollbackPlan,
) -> ProposalLifecycle:
    replay_proven = replay_activation_record(record)
    if replay_proven is not True:
        raise ToolingProposalError("proposal lifecycle is not replayable")
    if plan.validated is not True:
        raise ToolingProposalError("proposal lifecycle lacks validated rollback plan")
    return ProposalLifecycle(
        proposal_id=record.proposal_id,
        status="complete",
        activation_record=record,
        rollback_plan=plan,
        replay_proven=True,
        rollback_validated=True,
    )


def evaluate_rollback_execution_request(
    lifecycle: ProposalLifecycle,
    *,
    governance_approved: bool,
) -> dict[str, object]:
    if lifecycle.status != "complete":
        return {"rollback_allowed": False, "reason": "lifecycle incomplete"}
    if lifecycle.rollback_validated is not True:
        return {"rollback_allowed": False, "reason": "rollback not validated"}
    if governance_approved is not True:
        return {
            "rollback_allowed": False,
            "reason": "governance approval required",
        }
    return {
        "rollback_allowed": False,
        "reason": "rollback execution requires protected activation layer",
        "rollback_ready": True,
    }


def evaluate_mutation_request(proposal: ToolingProposal | None) -> dict[str, object]:
    if proposal is None:
        return {
            "mutation_allowed": False,
            "reason": "no proposal",
            "activation_status": "blocked",
        }
    if proposal.activation.status != "ready":
        return {
            "mutation_allowed": False,
            "reason": "activation not ready",
            "activation_status": proposal.activation.status,
        }
    return {
        "mutation_allowed": False,
        "reason": "tooling cannot execute runtime mutation",
        "activation_status": proposal.activation.status,
        "requires_activation_layer": True,
    }


def apply_diff(
    state: dict[str, object],
    diff: tuple[dict[str, object], ...],
) -> dict[str, object]:
    result = dict(state)
    for operation in diff:
        op = operation.get("op")
        key = _top_level_key(str(operation.get("path", "")))
        if not key:
            raise ToolingProposalError("diff path must target a top-level key")
        if op in {"add", "replace"}:
            result[key] = operation.get("value")
        elif op == "remove":
            result.pop(key, None)
        else:
            raise ToolingProposalError(f"unsupported diff operation: {op}")
    return result


def invert_diff(
    diff: tuple[dict[str, object], ...],
    pre_state: dict[str, object],
) -> tuple[dict[str, object], ...]:
    inverse: list[dict[str, object]] = []
    for operation in reversed(diff):
        key = _top_level_key(str(operation.get("path", "")))
        if not key:
            raise ToolingProposalError("diff path must target a top-level key")
        if key in pre_state:
            inverse.append({"op": "replace", "path": f"/{key}", "value": pre_state[key]})
        else:
            inverse.append({"op": "remove", "path": f"/{key}"})
    return tuple(inverse)


def _top_level_key(path: str) -> str:
    stripped = path.strip()
    if not stripped.startswith("/"):
        return ""
    return stripped.strip("/").split("/", 1)[0]


def _proposal_violations(proposal: ToolingProposal) -> list[str]:
    violations: list[str] = []
    if proposal.schema != PROPOSAL_SCHEMA:
        violations.append("invalid proposal schema")
    if not proposal.intent.strip():
        violations.append("proposal intent is required")
    if proposal.actor not in ALLOWED_ACTORS:
        violations.append("invalid proposal actor")
    if proposal.change_set.change_type not in ALLOWED_CHANGE_TYPES:
        violations.append("invalid change type")
    if not proposal.change_set.target.strip():
        violations.append("change target is required")
    if not proposal.change_set.diff.strip():
        violations.append("structured diff is required")
    if proposal.change_set.target.startswith(PROTECTED_TARGET_PREFIXES):
        violations.append("protected target mutation is forbidden")
    if proposal.activation.status != "blocked":
        violations.append("new proposals must begin blocked")
    if proposal.governance.status != "pending":
        violations.append("new proposals must begin governance-pending")
    return violations


__all__ = [
    "ACTIVATION_STATUSES",
    "ALLOWED_ACTORS",
    "ALLOWED_CHANGE_TYPES",
    "GOVERNANCE_STATUSES",
    "LIFECYCLE_STATUSES",
    "PROPOSAL_SCHEMA",
    "PROTECTED_TARGET_PREFIXES",
    "VALIDATION_STATUSES",
    "ActivationRecord",
    "ActivationState",
    "ChangeSet",
    "GovernanceApproval",
    "ProposalValidation",
    "ProposalLifecycle",
    "RollbackPlan",
    "ToolingProposal",
    "ToolingProposalError",
    "activation_gate",
    "apply_diff",
    "approve_proposal",
    "build_activation_record",
    "build_rollback_plan",
    "complete_proposal_lifecycle",
    "emit_tooling_proposal",
    "evaluate_rollback_execution_request",
    "evaluate_mutation_request",
    "invert_diff",
    "proposal_hash",
    "reject_proposal",
    "replay_activation_record",
    "validate_rollback_plan",
    "validate_proposal",
]
