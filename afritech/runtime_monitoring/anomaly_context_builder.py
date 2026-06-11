from __future__ import annotations

import hashlib
import json


def build_anomaly_context(
    anomaly: dict[str, object],
    *,
    timestamp: str,
    event_trace: tuple[str, ...] = (),
    current_receipt: str = "",
    expected_receipt: str = "",
    affected_files: tuple[str, ...] = (),
    validator_failures: tuple[str, ...] = (),
) -> dict[str, object]:
    context = {
        "timestamp": timestamp,
        "anomaly_type": anomaly.get("type"),
        "event_trace": event_trace,
        "current_receipt": current_receipt,
        "expected_receipt": expected_receipt,
        "affected_files": affected_files,
        "validator_failures": validator_failures,
        "replay_sufficient": True,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
    }
    encoded = json.dumps(context, sort_keys=True, separators=(",", ":")).encode()
    return {**context, "context_hash": hashlib.sha256(encoded).hexdigest()}


__all__ = ["build_anomaly_context"]
