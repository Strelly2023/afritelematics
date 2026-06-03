"""
AFRIPower dashboard metrics.

Metrics are read-only summaries derived from already-existing projection
objects and references.

They must not:
- validate truth
- execute runtime behavior
- mutate artifacts
- create authority
- influence replay/proof/CI/governance
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from afritech.afripower.contracts.read_only_contract import (
    assert_read_only_contract,
)
from afritech.afripower.dashboard.constants import (
    DASHBOARD_DISPLAY_ONLY,
    DASHBOARD_ENTERPRISE_INTELLIGENCE_ONLY,
    DASHBOARD_METRIC_TYPES,
    DASHBOARD_PROJECTION_ONLY,
    DASHBOARD_READ_ONLY,
    DASHBOARD_REFERENCE_ONLY,
    assert_dashboard_constants,
)
from afritech.afripower.graph.models import AFRIPowerGraph
from afritech.afripower.graph.query import (
    count_edges_by_relation,
    count_nodes_by_type,
)


class AFRIPowerDashboardMetricError(RuntimeError):
    """Raised when AFRIPower dashboard metrics cannot be computed."""


@dataclass(frozen=True)
class AFRIPowerDashboardMetric:
    """Immutable read-only dashboard metric."""

    metric_type: str
    value: int | float | str
    label: str | None = None

    def __post_init__(self) -> None:
        if self.metric_type not in DASHBOARD_METRIC_TYPES:
            raise AFRIPowerDashboardMetricError(
                f"unsupported dashboard metric_type: {self.metric_type}"
            )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "metric_type": self.metric_type,
            "label": self.label or self.metric_type,
            "value": self.value,
            "read_only": DASHBOARD_READ_ONLY,
            "reference_only": DASHBOARD_REFERENCE_ONLY,
            "display_only": DASHBOARD_DISPLAY_ONLY,
            "projection_only": DASHBOARD_PROJECTION_ONLY,
            "enterprise_intelligence_only": (
                DASHBOARD_ENTERPRISE_INTELLIGENCE_ONLY
            ),
            "creates_authority": False,
            "validates_truth": False,
            "executes_runtime": False,
            "mutates_artifacts": False,
        }


@dataclass(frozen=True)
class AFRIPowerDashboardMetricBundle:
    """Immutable read-only dashboard metric bundle."""

    metrics: tuple[AFRIPowerDashboardMetric, ...]

    def canonical_dict(self) -> dict[str, object]:
        return {
            "metric_count": len(self.metrics),
            "metrics": tuple(metric.canonical_dict() for metric in self.metrics),
            "read_only": DASHBOARD_READ_ONLY,
            "reference_only": DASHBOARD_REFERENCE_ONLY,
            "display_only": DASHBOARD_DISPLAY_ONLY,
            "projection_only": DASHBOARD_PROJECTION_ONLY,
            "enterprise_intelligence_only": (
                DASHBOARD_ENTERPRISE_INTELLIGENCE_ONLY
            ),
            "creates_authority": False,
            "validates_truth": False,
            "executes_runtime": False,
            "mutates_artifacts": False,
        }


def _assert_metric_boundary() -> None:
    assert_read_only_contract()
    assert_dashboard_constants()


def count_reference_payloads(
    payloads: Iterable[Mapping[str, object]],
) -> int:
    """Count provided payloads without interpreting authority."""

    _assert_metric_boundary()

    return sum(1 for _ in payloads)


def count_payloads_by_type(
    payloads: Iterable[Mapping[str, object]],
) -> dict[str, int]:
    """Count payloads by declared type/kind."""

    _assert_metric_boundary()

    counts: dict[str, int] = {}

    for payload in payloads:
        raw_type = (
            payload.get("receipt_type")
            or payload.get("proof_type")
            or payload.get("artifact_type")
            or payload.get("type")
            or "unknown"
        )
        key = str(raw_type)
        counts[key] = counts.get(key, 0) + 1

    return dict(sorted(counts.items()))


def build_graph_metric_bundle(
    graph: AFRIPowerGraph,
) -> AFRIPowerDashboardMetricBundle:
    """Build read-only dashboard metrics from a graph."""

    _assert_metric_boundary()

    if not isinstance(graph, AFRIPowerGraph):
        raise AFRIPowerDashboardMetricError(
            "expected AFRIPowerGraph"
        )

    metrics = [
        AFRIPowerDashboardMetric(
            metric_type="node_count",
            label="Node count",
            value=len(graph.nodes),
        ),
        AFRIPowerDashboardMetric(
            metric_type="edge_count",
            label="Edge count",
            value=len(graph.edges),
        ),
    ]

    return AFRIPowerDashboardMetricBundle(metrics=tuple(metrics))


def build_reference_metric_bundle(
    payloads: Iterable[Mapping[str, object]],
) -> AFRIPowerDashboardMetricBundle:
    """Build read-only metrics from reference payloads."""

    _assert_metric_boundary()

    materialized = tuple(payloads)

    receipt_count = sum(
        1
        for payload in materialized
        if (
            payload.get("receipt_id")
            or payload.get("receipt_type")
            or payload.get("type") == "receipt"
        )
    )

    proof_reference_count = sum(
        1
        for payload in materialized
        if (
            payload.get("proof_id")
            or payload.get("proof_type")
            or payload.get("type") == "proof"
        )
    )

    traceability_reference_count = sum(
        1
        for payload in materialized
        if payload.get("traceability") or payload.get("references")
    )

    metrics = (
        AFRIPowerDashboardMetric(
            metric_type="receipt_count",
            label="Receipt count",
            value=receipt_count,
        ),
        AFRIPowerDashboardMetric(
            metric_type="proof_reference_count",
            label="Proof reference count",
            value=proof_reference_count,
        ),
        AFRIPowerDashboardMetric(
            metric_type="traceability_reference_count",
            label="Traceability reference count",
            value=traceability_reference_count,
        ),
    )

    return AFRIPowerDashboardMetricBundle(metrics=metrics)


def build_complete_dashboard_metrics(
    *,
    graph: AFRIPowerGraph,
    references: Iterable[Mapping[str, object]] = tuple(),
    insight_count: int = 0,
) -> dict[str, object]:
    """Build deterministic read-only dashboard metrics."""

    _assert_metric_boundary()

    graph_bundle = build_graph_metric_bundle(graph)
    reference_bundle = build_reference_metric_bundle(references)

    node_type_counts = count_nodes_by_type(graph)
    edge_relation_counts = count_edges_by_relation(graph)

    metrics = (
        *graph_bundle.metrics,
        *reference_bundle.metrics,
        AFRIPowerDashboardMetric(
            metric_type="insight_count",
            label="Insight count",
            value=insight_count,
        ),
    )

    return {
        "metrics": tuple(metric.canonical_dict() for metric in metrics),
        "node_type_counts": node_type_counts,
        "edge_relation_counts": edge_relation_counts,
        "read_only": DASHBOARD_READ_ONLY,
        "reference_only": DASHBOARD_REFERENCE_ONLY,
        "display_only": DASHBOARD_DISPLAY_ONLY,
        "projection_only": DASHBOARD_PROJECTION_ONLY,
        "enterprise_intelligence_only": (
            DASHBOARD_ENTERPRISE_INTELLIGENCE_ONLY
        ),
        "creates_authority": False,
        "validates_truth": False,
        "executes_runtime": False,
        "mutates_artifacts": False,
    }


__all__ = [
    "AFRIPowerDashboardMetricError",
    "AFRIPowerDashboardMetric",
    "AFRIPowerDashboardMetricBundle",
    "count_reference_payloads",
    "count_payloads_by_type",
    "build_graph_metric_bundle",
    "build_reference_metric_bundle",
    "build_complete_dashboard_metrics",
]
