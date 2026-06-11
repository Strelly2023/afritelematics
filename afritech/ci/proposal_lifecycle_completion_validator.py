"""Validate activated proposals are replayable and rollback-ready."""

from __future__ import annotations

import sys

from afritech.afriprogramming.proposals import (
    ToolingProposalError,
    approve_proposal,
    build_activation_record,
    build_rollback_plan,
    complete_proposal_lifecycle,
    emit_tooling_proposal,
    validate_proposal,
    validate_rollback_plan,
)


VALIDATOR_NAME = "afritech.ci.proposal_lifecycle_completion_validator"


class ProposalLifecycleCompletionValidationError(RuntimeError):
    """Raised when proposal lifecycle completion semantics regress."""


def fail(message: str) -> None:
    raise ProposalLifecycleCompletionValidationError(message)


def validate_proposal_lifecycle_completion() -> None:
    from afritech.afriprogramming.proposals import activation_gate

    proposal = emit_tooling_proposal(
        origin="afriprogramming_cli",
        actor="user",
        intent="Lifecycle-complete tooling proposal",
        change_type="tooling_change",
        target="afritech/afriprogramming/tooling_surfaces.py",
        diff='{"op":"replace","path":"/lifecycle","value":"complete"}',
    )
    ready = activation_gate(
        approve_proposal(
            validate_proposal(proposal),
            approved_by=("governance-council",),
            timestamp="2026-06-06T00:00:00Z",
            approval_ref="GOV-LIFECYCLE-001",
        ),
        timestamp="2026-06-06T00:00:01Z",
    )
    record = build_activation_record(
        ready,
        pre_state={"lifecycle": "ready"},
        post_state={"lifecycle": "complete"},
        applied_diff=({"op": "replace", "path": "/lifecycle", "value": "complete"},),
        timestamp="2026-06-06T00:00:02Z",
    )
    plan = build_rollback_plan(record)

    try:
        complete_proposal_lifecycle(record, plan)
    except ToolingProposalError:
        pass
    else:
        fail("unvalidated rollback plan must not complete lifecycle")

    lifecycle = complete_proposal_lifecycle(record, validate_rollback_plan(record, plan))
    if lifecycle.status != "complete":
        fail("proposal lifecycle must become complete")
    if lifecycle.replay_proven is not True:
        fail("proposal lifecycle must prove replay")
    if lifecycle.rollback_validated is not True:
        fail("proposal lifecycle must validate rollback readiness")
    if lifecycle.rollback_execution_performed is not False:
        fail("lifecycle completion must not execute rollback")


def main() -> int:
    try:
        validate_proposal_lifecycle_completion()
        print("Proposal lifecycle completion validation PASSED")
        return 0
    except Exception as exc:
        print(f"Proposal lifecycle completion validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
