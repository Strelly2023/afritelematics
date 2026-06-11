"""Validate proposal emission stops at governance readiness."""

from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist import (
    emit_governance_ready_proposal,
    generate_context_aware_proposal,
)


VALIDATOR_NAME = "afritech.ci.afriprog_governance_readiness_validator"


class AfriprogGovernanceReadinessError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise AfriprogGovernanceReadinessError(message)


def validate_governance_readiness() -> None:
    proposal = generate_context_aware_proposal(
        intent="generate rollback plan",
        affected_files=("afritech/afriprogramming/proposals.py",),
    )
    emitted = emit_governance_ready_proposal(proposal)
    if emitted["emitted"] is not True:
        fail("proposal should emit as governance-ready")
    if emitted["governance_review_required"] is not True:
        fail("governance-ready proposal must still require review")
    if emitted["activation_allowed"] is not False:
        fail("governance-ready proposal must not activate")


def main() -> int:
    try:
        validate_governance_readiness()
        print("Afriprog governance readiness validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog governance readiness validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
