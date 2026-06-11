"""Validate inline fixes remain blocked until all gates pass."""

from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist import (
    generate_suggestion,
    validate_suggestion_gate,
)


VALIDATOR_NAME = "afritech.ci.afriprog_inline_fix_validation_gate"


class AfriprogInlineFixValidationGateError(RuntimeError):
    """Raised when inline fixes bypass validation gates."""


def fail(message: str) -> None:
    raise AfriprogInlineFixValidationGateError(message)


def validate_inline_fix_validation_gate() -> None:
    suggestion = generate_suggestion(
        kind="fix_failing_validator",
        intent="Fix failing proposal lifecycle validator",
        target="proposal_lifecycle_completion_validator",
    )
    blocked = validate_suggestion_gate(suggestion)
    if blocked["status"] != "blocked":
        fail("inline fix must be blocked before validators/replay/governance")
    if blocked["accepted"] is not False:
        fail("inline fix must not be accepted before gates")
    if not blocked["missing_validators"]:
        fail("inline fix must list required validators")

    required = suggestion.required_validators
    ready = validate_suggestion_gate(
        suggestion,
        validators_passed=required,
        replay_passed=True,
        governance_approved=True,
    )
    if ready["status"] != "ready_for_governed_proposal":
        fail("fully gated inline fix should only become proposal-ready")
    if ready["accepted"] is not False:
        fail("fully gated inline fix still must not be accepted directly")
    if ready["proposal_required"] is not True:
        fail("fully gated inline fix must still require a proposal")


def main() -> int:
    try:
        validate_inline_fix_validation_gate()
        print("Afriprog inline fix validation gate PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog inline fix validation gate FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
