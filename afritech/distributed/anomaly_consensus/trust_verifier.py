from __future__ import annotations

from afritech.distributed.anomaly_consensus.node_observer import sign_report


def verify_report(report: dict[str, object], public_keys: dict[str, str] | None = None) -> bool:
    node_id = str(report.get("node_id", ""))
    context_hash = str(report.get("context_hash", ""))
    expected = sign_report(node_id=node_id, context_hash=context_hash)
    return report.get("signature") == expected and bool(node_id and context_hash)


__all__ = ["verify_report"]
