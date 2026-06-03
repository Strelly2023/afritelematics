"""
AFRIPower dashboard serializers.

Serializers convert dashboard metrics and summaries into deterministic
read-only dictionaries.

They must not:
- mutate dashboard data
- validate truth
- create authority
- execute runtime behavior
- influence replay/proof/CI/governance
"""

from __future__ import annotations

from collections.abc import Mapping

from afritech.afripower.contracts.read_only_contract import (
    assert_read_only_contract,
)
from afritech.afripower.dashboard.constants import (
    DASHBOARD_DISPLAY_ONLY,
    DASHBOARD_ENTERPRISE_INTELLIGENCE_ONLY,
    DASHBOARD_PROJECTION_ONLY,
    DASHBOARD_READ_ONLY,
    DASHBOARD_REFERENCE_ONLY,
    assert_dashboard_constants,
)
from afritech.afripower.dashboard.metrics import (
    AFRIPowerDashboardMetric,
    AFRIPowerDashboardMetricBundle,
)


class AFRIPowerDashboardSerializationError(RuntimeError):
    """Raised when dashboard serialization fails."""


def _assert_dashboard_serialization_boundary() -> None:
    assert_read_only_contract()
    assert_dashboard_constants()


def _boundary_metadata() -> dict[str, object]:
    return {
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
        "mutates_dashboard": False,
        "mutates_artifacts": False,
        "influences_runtime": False,
        "influences_replay": False,
        "influences_proof": False,
        "influences_ci": False,
        "influences_governance": False,
    }


def serialize_dashboard_metric(
    metric: AFRIPowerDashboardMetric,
) -> dict[str, object]:
    """Serialize one dashboard metric deterministically."""

    _assert_dashboard_serialization_boundary()

    if not isinstance(metric, AFRIPowerDashboardMetric):
        raise AFRIPowerDashboardSerializationError(
            "expected AFRIPowerDashboardMetric"
        )

    data = metric.canonical_dict()
    data.update(_boundary_metadata())
    return data


def serialize_dashboard_metric_bundle(
    bundle: AFRIPowerDashboardMetricBundle,
) -> dict[str, object]:
    """Serialize a dashboard metric bundle deterministically."""

    _assert_dashboard_serialization_boundary()

    if not isinstance(bundle, AFRIPowerDashboardMetricBundle):
        raise AFRIPowerDashboardSerializationError(
            "expected AFRIPowerDashboardMetricBundle"
        )

    data = bundle.canonical_dict()
    data.update(_boundary_metadata())
    data["metrics"] = tuple(
        serialize_dashboard_metric(metric)
        for metric in bundle.metrics
    )
    return data


def serialize_dashboard_payload(
    payload: Mapping[str, object],
) -> dict[str, object]:
    """
    Serialize an already-built dashboard payload.

    This preserves existing fields while enforcing AFRIPower dashboard
    boundary metadata.
    """

    _assert_dashboard_serialization_boundary()

    if not isinstance(payload, Mapping):
        raise AFRIPowerDashboardSerializationError(
            "dashboard payload must be a mapping"
        )

    data = dict(payload)
    data.update(_boundary_metadata())
    return data


def serialize_dashboard_table(
    rows: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    """
    Serialize read-only dashboard table rows.

    Rows are copied into tuples of dictionaries to avoid mutation through
    caller-owned objects.
    """

    _assert_dashboard_serialization_boundary()

    serialized_rows = tuple(dict(row) for row in rows)

    return {
        "row_count": len(serialized_rows),
        "rows": serialized_rows,
        **_boundary_metadata(),
    }


def ensure_dashboard_boundary(
    payload: Mapping[str, object],
) -> None:
    """Fail closed if a serialized dashboard payload violates boundaries."""

    required_true = (
        "read_only",
        "reference_only",
        "display_only",
        "projection_only",
        "enterprise_intelligence_only",
    )

    required_false = (
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
    )

    for key in required_true:
        if payload.get(key) is not True:
            raise AFRIPowerDashboardSerializationError(
                f"dashboard payload field must be true: {key}"
            )

    for key in required_false:
        if payload.get(key) is not False:
            raise AFRIPowerDashboardSerializationError(
                f"dashboard payload field must be false: {key}"
            )


__all__ = [
    "AFRIPowerDashboardSerializationError",
    "serialize_dashboard_metric",
    "serialize_dashboard_metric_bundle",
    "serialize_dashboard_payload",
    "serialize_dashboard_table",
    "ensure_dashboard_boundary",
]
