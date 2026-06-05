from __future__ import annotations

from typing import Dict, List


class MetricsCollector:
    def __init__(self) -> None:
        self._node_metrics: List[Dict[str, object]] = []
        self._execution_metrics: List[Dict[str, object]] = []

    def record_node(self, metrics) -> None:
        self._node_metrics.append(metrics.to_dict() if hasattr(metrics, "to_dict") else dict(metrics))

    def record_execution(self, metrics) -> None:
        self._execution_metrics.append(metrics.to_dict() if hasattr(metrics, "to_dict") else dict(metrics))

    def snapshot(self) -> Dict[str, object]:
        return {
            "nodes": list(self._node_metrics),
            "executions": list(self._execution_metrics),
            "node_count": len(self._node_metrics),
            "execution_count": len(self._execution_metrics),
        }

    def reset(self) -> None:
        self._node_metrics.clear()
        self._execution_metrics.clear()
