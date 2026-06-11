"""Validate the final activation gate for governed tooling proposals."""

from __future__ import annotations

import sys

from afritech.afriprogramming.proposals import (
    ToolingProposalError,
    activation_gate,
    approve_proposal,
    emit_tooling_proposal,
    evaluate_mutation_request,
    validate_proposal,
)


VALIDATOR_NAME = "afritech.ci.tooling_activation_gate_validator"


class ToolingActivationGateValidationError(RuntimeError):
    """Raised when tooling activation semantics regress."""


def fail(message: str) -> None:
    raise ToolingActivationGateValidationError(message)


def validate_tooling_activation_gate() -> None:
    proposal = emit_tooling_proposal(
        origin="afriprogramming_cli",
        actor="user",
        intent="Prepare CLI validation enhancement",
        change_type="tooling_change",
        target="afritech/afriprogramming/tooling_surfaces.py",
        diff='{"op":"add","path":"/commands/-","value":"afri propose"}',
    )

    try:
        activation_gate(proposal, timestamp="2026-06-06T00:00:00Z")
    except ToolingProposalError:
        pass
    else:
        fail("unvalidated proposal must not pass activation")

    validated = validate_proposal(proposal)
    try:
        activation_gate(validated, timestamp="2026-06-06T00:00:00Z")
    except ToolingProposalError:
        pass
    else:
        fail("unapproved proposal must not pass activation")

    approved = approve_proposal(
        validated,
        approved_by=("governance-council",),
        timestamp="2026-06-06T00:00:00Z",
        approval_ref="GOV-ACTIVATE-001",
    )
    ready = activation_gate(approved, timestamp="2026-06-06T00:00:01Z")

    if ready.activation.status != "ready":
        fail("validated and approved proposal must become activation-ready")
    if ready.activation.execution_performed is not False:
        fail("activation gate must not execute runtime mutation")

    decision = evaluate_mutation_request(ready)
    if decision["mutation_allowed"] is not False:
        fail("tooling must not gain direct runtime mutation authority")
    if decision["requires_activation_layer"] is not True:
        fail("ready proposals must still require the activation layer")


def main() -> int:
    try:
        validate_tooling_activation_gate()
        print("Tooling activation gate validation PASSED")
        return 0
    except Exception as exc:
        print(f"Tooling activation gate validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
