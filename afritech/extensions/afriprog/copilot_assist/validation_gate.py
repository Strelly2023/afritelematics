from __future__ import annotations

from afritech.extensions.afriprog.copilot_assist.safety_classifier import (
    classify_suggestion,
)
from afritech.extensions.afriprog.copilot_assist.suggestion_model import (
    CopilotSuggestion,
)


def validate_suggestion_gate(
    suggestion: CopilotSuggestion,
    *,
    validators_passed: tuple[str, ...] = (),
    replay_passed: bool = False,
    governance_approved: bool = False,
) -> dict[str, object]:
    classification = classify_suggestion(suggestion)
    required = set(classification["required_validators"])
    passed = set(validators_passed)
    missing = tuple(sorted(required - passed))

    if classification["violations"]:
        return {
            "status": "rejected",
            "accepted": False,
            "missing_validators": missing,
            "replay_required": True,
            "governance_required": True,
        }

    if missing or not replay_passed or not governance_approved:
        return {
            "status": "blocked",
            "accepted": False,
            "missing_validators": missing,
            "replay_required": not replay_passed,
            "governance_required": not governance_approved,
        }

    return {
        "status": "ready_for_governed_proposal",
        "accepted": False,
        "missing_validators": (),
        "replay_required": False,
        "governance_required": False,
        "proposal_required": True,
    }


__all__ = ["validate_suggestion_gate"]
