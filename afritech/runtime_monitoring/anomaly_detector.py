from __future__ import annotations


def detect_anomalies(events: dict[str, object]) -> tuple[dict[str, object], ...]:
    anomalies: list[dict[str, object]] = []
    if events.get("validation_failures"):
        anomalies.append({"type": "validation_failure", "source": "runtime_monitor"})
    if events.get("contract_mismatches"):
        anomalies.append({"type": "contract_mismatch", "source": "runtime_monitor"})
    if events.get("replay_mismatches"):
        anomalies.append({"type": "replay_mismatch", "source": "runtime_monitor"})
    if events.get("timing_violations"):
        anomalies.append({"type": "timing_violation", "source": "runtime_monitor"})
    return tuple(anomalies)


__all__ = ["detect_anomalies"]
