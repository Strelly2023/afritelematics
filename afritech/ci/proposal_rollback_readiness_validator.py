"""Validate rollback plans exist and are governance-controlled."""

from __future__ import annotations

import sys

from afritech.afriprogramming.proposals import (
    approve_proposal,
    build_activation_record,
    build_rollback_plan,
    emit_tooling_proposal,
    evaluate_rollback_execution_request,
    validate_proposal,
    validate_rollback_plan,
)


VALIDATOR_NAME = "afritech.ci.proposal_rollback_readiness_validator"


class ProposalRollbackReadinessValidationError(RuntimeError):
    """Raised when rollback readiness guarantees regress."""


def fail(message: str) -> None:
    raise ProposalRollbackReadinessValidationError(message)


def _record():
    from afritech.afriprogramming.proposals import activation_gate

    proposal = emit_tooling_proposal(
        origin="multi_agent_orchestrator",
        actor="system",
        intent="Rollback-ready tooling change",
        change_type="tooling_change",
        target="afritech/afriprogramming/tooling_surfaces.py",
        diff='{"op":"replace","path":"/mode","value":"governed"}',
    )
    ready = activation_gate(
        approve_proposal(
            validate_proposal(proposal),
            approved_by=("governance-council",),
            timestamp="2026-06-06T00:00:00Z",
            approval_ref="GOV-ROLLBACK-001",
        ),
        timestamp="2026-06-06T00:00:01Z",
    )
    return build_activation_record(
        ready,
        pre_state={"mode": "proposal"},
        post_state={"mode": "governed"},
        applied_diff=({"op": "replace", "path": "/mode", "value": "governed"},),
        timestamp="2026-06-06T00:00:02Z",
    )


def validate_proposal_rollback_readiness() -> None:
    record = _record()
    plan = build_rollback_plan(record)
    validated = validate_rollback_plan(record, plan)

    if validated.validated is not True:
        fail("rollback plan must validate")
    if validated.governance_required is not True:
        fail("rollback execution must require governance")
    if not validated.rollback_diff:
        fail("rollback plan must include a rollback diff")

    from afritech.afriprogramming.proposals import complete_proposal_lifecycle

    lifecycle = complete_proposal_lifecycle(record, validated)
    blocked = evaluate_rollback_execution_request(
        lifecycle,
        governance_approved=False,
    )
    if blocked["rollback_allowed"] is not False:
        fail("rollback execution must be blocked without governance approval")

    approved_but_protected = evaluate_rollback_execution_request(
        lifecycle,
        governance_approved=True,
    )
    if approved_but_protected["rollback_allowed"] is not False:
        fail("rollback execution must remain outside tooling authority")
    if approved_but_protected["rollback_ready"] is not True:
        fail("approved rollback request must report rollback readiness")


def main() -> int:
    try:
        validate_proposal_rollback_readiness()
        print("Proposal rollback readiness validation PASSED")
        return 0
    except Exception as exc:
        print(f"Proposal rollback readiness validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
