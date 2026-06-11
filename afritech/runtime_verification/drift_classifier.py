from __future__ import annotations


DRIFT_SEVERITY = {
    "state_violation": "HIGH",
    "temporal_violation": "HIGH",
    "ordering_violation": "HIGH",
    "frequency_violation": "MEDIUM",
}


def classify_drift(drift: dict[str, object]) -> dict[str, object]:
    drift_type = str(drift.get("type", "unknown"))
    severity = DRIFT_SEVERITY.get(drift_type, "LOW")
    return {
        **drift,
        "severity": severity,
        "confidence": 0.95 if severity in {"HIGH", "CRITICAL"} else 0.75,
        "requires_replay": True,
        "requires_rollback": severity in {"HIGH", "CRITICAL"},
        "decision_authority": False,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
        "rollback_execution_allowed": False,
    }


__all__ = ["DRIFT_SEVERITY", "classify_drift"]
