"""Validate explicit governance approval before proposal activation."""

from __future__ import annotations

import sys

from afritech.afriprogramming.proposals import (
    ToolingProposalError,
    approve_proposal,
    emit_tooling_proposal,
    reject_proposal,
    validate_proposal,
)


VALIDATOR_NAME = "afritech.ci.governance_approval_flow_validator"


class GovernanceApprovalFlowValidationError(RuntimeError):
    """Raised when governance approval semantics regress."""


def fail(message: str) -> None:
    raise GovernanceApprovalFlowValidationError(message)


def _safe_validated_proposal():
    proposal = emit_tooling_proposal(
        origin="multi_agent_orchestrator",
        actor="system",
        intent="Prepare governed validator improvement proposal",
        change_type="validator_change",
        target="afritech/ci/example_validator.py",
        diff='{"op":"add","path":"/guard","value":"proposal-only"}',
    )
    validated = validate_proposal(proposal)
    if validated.validation.status != "pass":
        fail("safe proposal must pass before governance validation")
    return validated


def validate_governance_approval_flow() -> None:
    validated = _safe_validated_proposal()

    try:
        approve_proposal(
            validated,
            approved_by=(),
            timestamp="2026-06-06T00:00:00Z",
            approval_ref="GOV-EMPTY",
        )
    except ToolingProposalError:
        pass
    else:
        fail("empty governance approval must be rejected")

    approved = approve_proposal(
        validated,
        approved_by=("governance-council",),
        timestamp="2026-06-06T00:00:00Z",
        approval_ref="GOV-AFRIPROG-001",
    )
    if approved.governance.status != "approved":
        fail("explicit governance approval must set approved status")
    if approved.governance.approved_by != ("governance-council",):
        fail("approval signer must be retained")

    rejected = reject_proposal(validated, approval_ref="GOV-REJECT-001")
    if rejected.governance.status != "rejected":
        fail("proposal rejection must be explicit")

    unvalidated = emit_tooling_proposal(
        origin="multi_agent_orchestrator",
        actor="system",
        intent="Unvalidated proposal",
        change_type="tooling_change",
        target="afritech/afriprogramming/tooling_surfaces.py",
        diff='{"op":"add","path":"/x","value":"y"}',
    )
    try:
        approve_proposal(
            unvalidated,
            approved_by=("governance-council",),
            timestamp="2026-06-06T00:00:00Z",
            approval_ref="GOV-UNVALIDATED",
        )
    except ToolingProposalError:
        pass
    else:
        fail("unvalidated proposal must not be approval-eligible")


def main() -> int:
    try:
        validate_governance_approval_flow()
        print("Governance approval flow validation PASSED")
        return 0
    except Exception as exc:
        print(f"Governance approval flow validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
