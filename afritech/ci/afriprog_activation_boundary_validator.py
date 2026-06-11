"""Validate context-aware proposals cannot cross activation boundary."""

from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist import generate_context_aware_proposal


VALIDATOR_NAME = "afritech.ci.afriprog_activation_boundary_validator"


class AfriprogActivationBoundaryError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise AfriprogActivationBoundaryError(message)


def validate_activation_boundary() -> None:
    proposal = generate_context_aware_proposal(
        intent="prepare activation-safe proposal",
        affected_files=("afritech/cli/main.py",),
    )
    payload = proposal.canonical_dict()
    if payload["activation_allowed"] is not False:
        fail("context-aware proposal must not be activation")
    if payload["runtime_mutation_allowed"] is not False:
        fail("context-aware proposal must not mutate runtime")
    if payload["rollback_execution_allowed"] is not False:
        fail("context-aware proposal must not execute rollback")


def main() -> int:
    try:
        validate_activation_boundary()
        print("Afriprog activation boundary validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog activation boundary validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
