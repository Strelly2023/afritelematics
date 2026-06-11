"""Validate AI suggestions never become authority."""

from __future__ import annotations

import sys

from afritech.extensions.afriprog.copilot_assist import (
    ASSISTANCE_KINDS,
    classify_suggestion,
    generate_suggestion,
)


VALIDATOR_NAME = "afritech.ci.afriprog_ai_suggestion_non_authority_validator"


class AfriprogAISuggestionNonAuthorityError(RuntimeError):
    """Raised when AI suggestions gain authority."""


def fail(message: str) -> None:
    raise AfriprogAISuggestionNonAuthorityError(message)


def validate_ai_suggestion_non_authority() -> None:
    for kind in ASSISTANCE_KINDS:
        suggestion = generate_suggestion(kind=kind, intent="demo", target="target")
        payload = suggestion.canonical_dict()
        classification = classify_suggestion(suggestion)

        if classification["admissible"] is not False:
            fail(f"{kind} suggestion must not be self-admissible")
        if classification["confidence_is_certification"] is not False:
            fail(f"{kind} confidence must not be certification")
        for key in (
            "execution_authority",
            "proof_authority",
            "replay_authority",
            "governance_authority",
        ):
            if payload[key] is not False:
                fail(f"{kind} gained {key}")
        if payload["accepted"] is not False:
            fail(f"{kind} must not be accepted code")


def main() -> int:
    try:
        validate_ai_suggestion_non_authority()
        print("Afriprog AI suggestion non-authority validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog AI suggestion non-authority validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
