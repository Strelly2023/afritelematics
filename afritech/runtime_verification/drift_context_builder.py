from __future__ import annotations

import hashlib
import json


def build_drift_context(
    drift: dict[str, object],
    *,
    timestamp: str,
    affected_files: tuple[str, ...] = (),
) -> dict[str, object]:
    context = {
        "timestamp": timestamp,
        "drift_type": drift.get("type"),
        "contract": drift.get("contract"),
        "violation_point": drift.get("event"),
        "expected_behavior": drift.get("expected_behavior"),
        "observed_behavior": drift.get("observed_behavior"),
        "event_trace": tuple(drift.get("trace", ())),
        "affected_files": affected_files,
        "replay_sufficient": True,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
        "rollback_execution_allowed": False,
    }
    encoded = json.dumps(context, sort_keys=True, separators=(",", ":")).encode()
    return {**context, "context_hash": hashlib.sha256(encoded).hexdigest()}


__all__ = ["build_drift_context"]
