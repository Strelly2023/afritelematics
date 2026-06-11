from __future__ import annotations


SEVERITY_BY_TYPE = {
    "validation_failure": "MEDIUM",
    "contract_mismatch": "HIGH",
    "replay_mismatch": "HIGH",
    "timing_violation": "MEDIUM",
}


def classify_anomaly(anomaly: dict[str, object]) -> dict[str, object]:
    anomaly_type = str(anomaly.get("type", "unknown"))
    severity = SEVERITY_BY_TYPE.get(anomaly_type, "LOW")
    return {
        **anomaly,
        "severity": severity,
        "requires_replay": anomaly_type in {"contract_mismatch", "replay_mismatch"},
        "requires_rollback": severity in {"HIGH", "CRITICAL"},
        "decision_authority": False,
    }


__all__ = ["SEVERITY_BY_TYPE", "classify_anomaly"]
