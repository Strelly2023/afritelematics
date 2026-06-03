from __future__ import annotations

import pytest

from afritech.afripower.dashboard.metrics import (
    AFRIPowerDashboardMetric,
    AFRIPowerDashboardMetricBundle,
)
from afritech.afripower.dashboard.serializers import (
    AFRIPowerDashboardSerializationError,
    ensure_dashboard_boundary,
    serialize_dashboard_metric,
    serialize_dashboard_metric_bundle,
    serialize_dashboard_payload,
    serialize_dashboard_table,
)


def test_serialize_dashboard_metric():
    metric = AFRIPowerDashboardMetric(
        metric_type="node_count",
        value=5,
    )

    data = serialize_dashboard_metric(metric)

    assert data["metric_type"] == "node_count"
    assert data["value"] == 5

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True

    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_dashboard"] is False
    assert data["mutates_artifacts"] is False


def test_serialize_dashboard_metric_rejects_wrong_type():
    with pytest.raises(AFRIPowerDashboardSerializationError):
        serialize_dashboard_metric("bad")  # type: ignore[arg-type]


def test_serialize_dashboard_metric_bundle():
    bundle = AFRIPowerDashboardMetricBundle(
        metrics=(
            AFRIPowerDashboardMetric(
                metric_type="node_count",
                value=3,
            ),
            AFRIPowerDashboardMetric(
                metric_type="edge_count",
                value=2,
            ),
        )
    )

    data = serialize_dashboard_metric_bundle(bundle)

    assert data["metric_count"] == 2
    assert len(data["metrics"]) == 2

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True

    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_dashboard"] is False


def test_serialize_dashboard_metric_bundle_rejects_wrong_type():
    with pytest.raises(AFRIPowerDashboardSerializationError):
        serialize_dashboard_metric_bundle("bad")  # type: ignore[arg-type]


def test_serialize_dashboard_payload():
    payload = {
        "dashboard": "summary",
        "count": 5,
    }

    data = serialize_dashboard_payload(payload)

    assert data["dashboard"] == "summary"
    assert data["count"] == 5

    assert data["read_only"] is True
    assert data["reference_only"] is True
    assert data["display_only"] is True
    assert data["projection_only"] is True
    assert data["enterprise_intelligence_only"] is True

    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False
    assert data["mutates_dashboard"] is False


def test_serialize_dashboard_payload_rejects_non_mapping():
    with pytest.raises(AFRIPowerDashboardSerializationError):
        serialize_dashboard_payload("bad")  # type: ignore[arg-type]


def test_serialize_dashboard_table():
    data = serialize_dashboard_table(
        (
            {
                "name": "Execution",
                "count": 2,
            },
            {
                "name": "Proof",
                "count": 1,
            },
        )
    )

    assert data["row_count"] == 2
    assert len(data["rows"]) == 2

    assert data["rows"][0]["name"] == "Execution"
    assert data["rows"][1]["name"] == "Proof"

    assert data["read_only"] is True
    assert data["creates_authority"] is False
    assert data["validates_truth"] is False
    assert data["executes_runtime"] is False


def test_ensure_dashboard_boundary_accepts_valid_metric():
    payload = serialize_dashboard_metric(
        AFRIPowerDashboardMetric(
            metric_type="node_count",
            value=1,
        )
    )

    ensure_dashboard_boundary(payload)


@pytest.mark.parametrize(
    "field",
    (
        "read_only",
        "reference_only",
        "display_only",
        "projection_only",
        "enterprise_intelligence_only",
    ),
)
def test_ensure_dashboard_boundary_rejects_required_true_fields(
    field: str,
):
    payload = serialize_dashboard_payload({"demo": True})
    payload[field] = False

    with pytest.raises(AFRIPowerDashboardSerializationError):
        ensure_dashboard_boundary(payload)


@pytest.mark.parametrize(
    "field",
    (
        "creates_authority",
        "validates_truth",
        "executes_runtime",
        "mutates_dashboard",
        "mutates_artifacts",
        "influences_runtime",
        "influences_replay",
        "influences_proof",
        "influences_ci",
        "influences_governance",
    ),
)
def test_ensure_dashboard_boundary_rejects_required_false_fields(
    field: str,
):
    payload = serialize_dashboard_payload({"demo": True})
    payload[field] = True

    with pytest.raises(AFRIPowerDashboardSerializationError):
        ensure_dashboard_boundary(payload)


def test_dashboard_serialization_is_deterministic():
    metric = AFRIPowerDashboardMetric(
        metric_type="node_count",
        value=5,
    )

    first = serialize_dashboard_metric(metric)
    second = serialize_dashboard_metric(metric)

    assert first == second
