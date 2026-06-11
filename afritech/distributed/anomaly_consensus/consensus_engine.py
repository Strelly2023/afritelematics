from __future__ import annotations

from collections import Counter, defaultdict


def compute_consensus(
    reports: tuple[dict[str, object], ...],
    *,
    total_nodes: int,
    min_quorum: int = 2,
) -> tuple[dict[str, object], ...]:
    grouped: dict[tuple[object, object], list[dict[str, object]]] = defaultdict(list)
    for report in reports:
        grouped[(report.get("anomaly_type"), report.get("context_hash"))].append(report)

    consensus: list[dict[str, object]] = []
    for (anomaly_type, context_hash), group in grouped.items():
        if len(group) < min_quorum:
            continue
        severities = Counter(str(report.get("severity", "LOW")) for report in group)
        consensus.append(
            {
                "anomaly_type": anomaly_type,
                "context_hash": context_hash,
                "node_count": len(group),
                "total_nodes": total_nodes,
                "confidence": len(group) / total_nodes,
                "severity": severities.most_common(1)[0][0],
                "reports": tuple(group),
                "consensus_authority": "non_authoritative",
                "activation_allowed": False,
                "runtime_mutation_allowed": False,
            }
        )
    return tuple(consensus)


__all__ = ["compute_consensus"]
