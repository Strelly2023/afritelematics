from __future__ import annotations


def detect_drift(
    observation: dict[str, object],
    evaluation: dict[str, object],
) -> dict[str, object] | None:
    if evaluation.get("compliant") is True:
        return None
    return {
        "type": "state_violation",
        "contract": evaluation.get("contract"),
        "event": evaluation.get("event"),
        "expected_behavior": evaluation.get("expected_behavior"),
        "observed_behavior": evaluation.get("observed_behavior"),
        "trace": observation.get("trace", ()),
        "enforcement_authority": False,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
        "rollback_execution_allowed": False,
    }


__all__ = ["detect_drift"]
