"""Validate context-aware tooling proposals remain non-authoritative."""

from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist import generate_context_aware_proposal


VALIDATOR_NAME = "afritech.ci.afriprog_tooling_proposal_non_authority_validator"


class AfriprogToolingProposalNonAuthorityError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise AfriprogToolingProposalNonAuthorityError(message)


def validate_tooling_proposal_non_authority() -> None:
    proposal = generate_context_aware_proposal(
        intent="suggest refactor",
        affected_files=("afritech/extensions/afriprog/example.py",),
    )
    payload = proposal.canonical_dict()
    for key in (
        "activation_allowed",
        "runtime_mutation_allowed",
        "approval_granted",
        "rollback_execution_allowed",
    ):
        if payload[key] is not False:
            fail(f"context-aware proposal must keep {key}=False")


def main() -> int:
    try:
        validate_tooling_proposal_non_authority()
        print("Afriprog tooling proposal non-authority validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog tooling proposal non-authority validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
