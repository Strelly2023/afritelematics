"""Validate auto-validation prepares proposals without authority."""

from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist import (
    generate_context_aware_proposal,
    validate_context_proposal,
)


VALIDATOR_NAME = "afritech.ci.afriprog_auto_validation_loop_validator"


class AfriprogAutoValidationLoopError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise AfriprogAutoValidationLoopError(message)


def validate_auto_validation_loop() -> None:
    proposal = generate_context_aware_proposal(
        intent="fix validator failure",
        affected_files=("afritech/ci/example_validator.py",),
        from_failure="proposal_lifecycle_completion_validator failed",
    )
    validation = validate_context_proposal(proposal)
    if validation["status"] != "ready_for_governance":
        fail("auto-validation should prepare governance-ready proposal")
    if validation["approval_granted"] is not False:
        fail("auto-validation must not approve proposal")
    if validation["activation_allowed"] is not False:
        fail("auto-validation must not activate proposal")
    if validation["runtime_mutation_allowed"] is not False:
        fail("auto-validation must not mutate runtime")


def main() -> int:
    try:
        validate_auto_validation_loop()
        print("Afriprog auto-validation loop validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog auto-validation loop validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
