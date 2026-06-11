"""Validate context-aware AfriProg proposal generation."""

from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist import (
    generate_context_aware_proposal,
    inspect_context_proposal,
)


VALIDATOR_NAME = "afritech.ci.afriprog_context_proposal_validator"


class AfriprogContextProposalValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise AfriprogContextProposalValidationError(message)


def validate_context_proposal_surface() -> None:
    proposal = generate_context_aware_proposal(
        intent="add driver availability endpoint",
        affected_files=("afritech/api/driver.py",),
    )
    payload = inspect_context_proposal(proposal)
    if payload["governance_review_required"] is not True:
        fail("context proposal must require governance review")
    if payload["activation_allowed"] is not False:
        fail("context proposal must not allow activation")
    if payload["runtime_mutation_allowed"] is not False:
        fail("context proposal must not allow runtime mutation")
    if not payload["proposal"]["affected_files"]:
        fail("context proposal must retain affected file context")


def main() -> int:
    try:
        validate_context_proposal_surface()
        print("Afriprog context proposal validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog context proposal validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
