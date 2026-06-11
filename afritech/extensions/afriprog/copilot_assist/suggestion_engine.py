from __future__ import annotations

from afritech.extensions.afriprog.copilot_assist.safety_classifier import (
    required_validators_for,
)
from afritech.extensions.afriprog.copilot_assist.suggestion_model import (
    ASSISTANCE_KINDS,
    CopilotSuggestion,
    build_suggestion_id,
)


BODY_BY_KIND = {
    "inline_code_suggestion": "Proposed inline code change. Review required.",
    "context_file_analysis": "Context summary generated from repository signals.",
    "explain_this_code": "Explanation is advisory and is not proof.",
    "generate_tests": "Suggested tests. Test execution is still required.",
    "fix_failing_validator": "Suggested validator fix. Validator rerun is mandatory.",
    "generate_contract_binding": "Suggested contract_binding shape. Contract validator required.",
    "generate_replay_fixture": "Suggested replay fixture. Replay validator required.",
    "suggest_refactor": "Suggested refactor. Behavior preservation must be validated.",
    "create_rollback_plan": "Suggested rollback plan. Governance approval required.",
    "confidence_and_validators": "Confidence is advisory; validators decide acceptance.",
}


def generate_suggestion(
    *,
    kind: str,
    intent: str,
    target: str = "",
) -> CopilotSuggestion:
    if kind not in ASSISTANCE_KINDS:
        raise ValueError(f"unsupported Copilot assistance kind: {kind}")

    return CopilotSuggestion(
        suggestion_id=build_suggestion_id(kind, intent, target),
        kind=kind,
        intent=intent,
        target=target,
        body=BODY_BY_KIND[kind],
        confidence=_confidence_for(kind),
        required_validators=required_validators_for(kind),
        explanation=(
            "AI assistance may suggest this output, but contracts, validators, "
            "replay, and governance decide acceptance."
        ),
    )


def _confidence_for(kind: str) -> float:
    if kind in {"fix_failing_validator", "create_rollback_plan"}:
        return 0.58
    if kind in {"generate_contract_binding", "generate_replay_fixture"}:
        return 0.64
    return 0.72


__all__ = ["BODY_BY_KIND", "generate_suggestion"]
