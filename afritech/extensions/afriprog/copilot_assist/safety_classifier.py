from __future__ import annotations

from afritech.extensions.afriprog.copilot_assist.suggestion_model import (
    ASSISTANCE_KINDS,
    CopilotSuggestion,
)


BASE_REQUIRED_VALIDATORS = (
    "afritech.ci.afriprog_copilot_assist_validator",
    "afritech.ci.afriprog_ai_suggestion_non_authority_validator",
    "afritech.ci.afriprog_inline_fix_validation_gate",
)

KIND_VALIDATORS = {
    "fix_failing_validator": ("afritech.ci.constitutional_validation",),
    "generate_contract_binding": ("afritech.ci.driver_event_contract_binding_validator",),
    "generate_replay_fixture": ("afritech.ci.driver_contract_replay_validator",),
    "create_rollback_plan": ("afritech.ci.proposal_rollback_readiness_validator",),
    "generate_tests": ("pytest",),
}


def required_validators_for(kind: str) -> tuple[str, ...]:
    if kind not in ASSISTANCE_KINDS:
        raise ValueError(f"unsupported Copilot assistance kind: {kind}")
    return BASE_REQUIRED_VALIDATORS + KIND_VALIDATORS.get(kind, ())


def classify_suggestion(suggestion: CopilotSuggestion) -> dict[str, object]:
    payload = suggestion.canonical_dict()
    violations: list[str] = []

    if payload["authority"] != "developer_assistance_only":
        violations.append("suggestion gained authority")
    if payload["accepted"] is not False:
        violations.append("suggestion cannot be accepted directly")
    if payload["mutates_runtime"] is not False:
        violations.append("suggestion cannot mutate runtime")
    for key in (
        "execution_authority",
        "proof_authority",
        "replay_authority",
        "governance_authority",
    ):
        if payload[key] is not False:
            violations.append(f"suggestion cannot gain {key}")

    return {
        "admissible": False,
        "status": "requires_validation" if not violations else "rejected",
        "violations": tuple(violations),
        "required_validators": payload["required_validators"],
        "confidence_is_certification": False,
    }


__all__ = [
    "BASE_REQUIRED_VALIDATORS",
    "KIND_VALIDATORS",
    "classify_suggestion",
    "required_validators_for",
]
