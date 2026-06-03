from __future__ import annotations

import pytest

from afritech.afripower.dashboard.metrics import (
    AFRIPowerDashboardMetric,
    AFRIPowerDashboardMetricBundle,
    AFRIPowerDashboardMetricError,
    build_complete_dashboard_metrics,
    build_graph_metric_bundle,
    build_reference_metric_bundle,
    count_payloads_by_type,
    count_reference_payloads,
)
from afritech.afripower.graph.projection import (
    build_graph_projection_from_mappings,
)


def _sample_graph():
    return build_graph_projection_from_mappings(
        (
            {
                "execution_id": "exec.001",
                "traceability": [
                    {"type": "Proof", "id": "proof.001"},
                    {"type": "ADR", "id": "ADR-001"},
                ],
            },
        )
    )


def test_dashboard_metric_accepts_valid_type():
    metric = AFRIPowerDashboardMetric(
        metric_type="node_count",
        value=2,
    )

    assert metric.metric_type == "node_count"
    assert metric.value == 2


def test_dashboard_metric_rejects_invalid_type():
    with pytest.raises(AFRIPowerDashboardMetricError):
        AFRIPowerDashboardMetric(
            metric_type="invalid_metric",
            value=1,
        )


def test_dashboard_metric_canonical_dict_preserves_boundary():
    metric = AFRIPowerDashboardMetric(
        metric_type="node_count",
        value=2,
        label="Node count",
    )

    data = metric.canonical_dict()

    assert data["metric_type"] == "node_count"
    assert data["label"] == "Node count"
    assert data["value"] == 2
    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_artifacts"] is False


def test_dashboard_metric_defaults_label_to_type():
    metric = AFRIPowerDashboardMetric(
        metric_type="edge_count",
        value=3,
    )

    assert metric.canonical_dict()["label"] == "edge_count"


def test_dashboard_metric_bundle_canonical_dict():
    bundle = AFRIPowerDashboardMetricBundle(
        metrics=(
            AFRIPowerDashboardMetric(
                metric_type="node_count",
                value=2,
            ),
            AFRIPowerDashboardMetric(
                metric_type="edge_count",
                value=1,
            ),
        )
    )

    data = bundle.canonical_dict()

    assert data["metric_count"] == 2
    assert len(data["metrics"]) == 2
    assert data["read_only"] is True
    assert data["creates_authority"] is False


def test_count_reference_payloads():
    count = count_reference_payloads(
        (
            {"receipt_id": "receipt.001"},
            {"proof_id": "proof.001"},
        )
    )

    assert count == 2


def test_count_payloads_by_type():
    counts = count_payloads_by_type(
        (
            {"receipt_type": "receipt"},
            {"proof_type": "proof"},
            {"artifact_type": "execution"},
            {"type": "receipt"},
            {},
        )
    )

    assert counts == {
        "execution": 1,
        "proof": 1,
        "receipt": 2,
        "unknown": 1,
    }


def test_build_graph_metric_bundle():
    graph = _sample_graph()

    bundle = build_graph_metric_bundle(graph)
    data = bundle.canonical_dict()

    assert data["metric_count"] == 2
    values = {
        metric["metric_type"]: metric["value"]
        for metric in data["metrics"]
    }

    assert values["node_count"] == 3
    assert values["edge_count"] == 2


def test_build_graph_metric_bundle_rejects_wrong_type():
    with pytest.raises(AFRIPowerDashboardMetricError):
        build_graph_metric_bundle("bad")  # type: ignore[arg-type]


def test_build_reference_metric_bundle():
    bundle = build_reference_metric_bundle(
        (
            {"receipt_id": "receipt.001"},
            {"proof_id": "proof.001"},
            {
                "execution_id": "exec.001",
                "traceability": [
                    {"type": "Proof", "id": "proof.001"},
                ],
            },
        )
    )

    data = bundle.canonical_dict()
    values = {
        metric["metric_type"]: metric["value"]
        for metric in data["metrics"]
    }

    assert values["receipt_count"] == 1
    assert values["proof_reference_count"] == 1
    assert values["traceability_reference_count"] == 1


def test_build_complete_dashboard_metrics():
    graph = _sample_graph()

    data = build_complete_dashboard_metrics(
        graph=graph,
        references=(
            {"receipt_id": "receipt.001"},
            {"proof_id": "proof.001"},
            {
                "execution_id": "exec.001",
                "traceability": [
                    {"type": "Proof", "id": "proof.001"},
                ],
            },
        ),
        insight_count=4,
    )

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_artifacts"] is False

    metric_values = {
        metric["metric_type"]: metric["value"]
        for metric in data["metrics"]
    }

    assert metric_values["node_count"] == 3
    assert metric_values["edge_count"] == 2
    assert metric_values["receipt_count"] == 1
    assert metric_values["proof_reference_count"] == 1
    assert metric_values["traceability_reference_count"] == 1
    assert metric_values["insight_count"] == 4

    assert data["node_type_counts"] == {
        "ADR": 1,
        "Execution": 1,
        "Proof": 1,
    }
    assert data["edge_relation_counts"] == {
        "references": 2,
    }


def test_build_complete_dashboard_metrics_is_deterministic():
    graph = _sample_graph()
    references = (
        {"receipt_id": "receipt.001"},
        {"proof_id": "proof.001"},
    )

    first = build_complete_dashboard_metrics(
        graph=graph,
        references=references,
        insight_count=1,
    )
    second = build_complete_dashboard_metrics(
        graph=graph,
        references=references,
        insight_count=1,
    )

    assert first == second
