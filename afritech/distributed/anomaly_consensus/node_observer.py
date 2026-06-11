from __future__ import annotations

import hashlib


def observe_anomaly(
    *,
    node_id: str,
    timestamp: str,
    anomaly_type: str,
    severity: str,
    context_hash: str,
) -> dict[str, object]:
    signature = sign_report(node_id=node_id, context_hash=context_hash)
    return {
        "node_id": node_id,
        "timestamp": timestamp,
        "anomaly_type": anomaly_type,
        "severity": severity,
        "context_hash": context_hash,
        "signature": signature,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
    }


def sign_report(*, node_id: str, context_hash: str) -> str:
    return hashlib.sha256(f"{node_id}:{context_hash}".encode()).hexdigest()


__all__ = ["observe_anomaly", "sign_report"]
