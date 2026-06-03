"""
AFRIPower dashboard services.

Services compose read-only graph, metric, and serializer outputs into
dashboard-ready payloads.

They must not:
- execute runtime behavior
- validate truth
- mutate artifacts
- create authority
- influence replay/proof/CI/governance
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

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
    dashboard_metadata,
)
from afritech.afripower.dashboard.metrics import (
    build_complete_dashboard_metrics,
)
from afritech.afripower.dashboard.serializers import (
    ensure_dashboard_boundary,
    serialize_dashboard_payload,
)
from afritech.afripower.graph.projection import (
    build_graph_projection_from_mappings,
)
from afritech.afripower.graph.serializers import (
    serialize_graph,
    serialize_graph_summary,
)
from afritech.afripower.dashboard.serializers import (
    AFRIPowerDashboardSerializationError,
    ensure_dashboard_boundary,
    serialize_dashboard_payload,
)

class AFRIPowerDashboardServiceError(RuntimeError):
    """Raised when dashboard service composition fails."""


def _assert_dashboard_service_boundary() -> None:
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


def build_dashboard_overview(
    references: Iterable[Mapping[str, object]],
    *,
    insight_count: int = 0,
) -> dict[str, object]:
    """
    Build a complete read-only AFRIPower dashboard overview.

    Input references are treated as already-existing artifacts.
    This function does not validate their truth.
    """

    _assert_dashboard_service_boundary()

    materialized_references = tuple(references)

    graph = build_graph_projection_from_mappings(materialized_references)
    graph_payload = serialize_graph(graph)
    graph_summary = serialize_graph_summary(graph)
    metrics = build_complete_dashboard_metrics(
        graph=graph,
        references=materialized_references,
        insight_count=insight_count,
    )

    payload = {
        "dashboard": dashboard_metadata(),
        "graph": graph_payload,
        "graph_summary": graph_summary,
        "metrics": metrics,
        "reference_count": len(materialized_references),
        **_boundary_metadata(),
    }

    serialized = serialize_dashboard_payload(payload)
    ensure_dashboard_boundary(serialized)

    return serialized


def build_dashboard_summary(
    references: Iterable[Mapping[str, object]],
    *,
    insight_count: int = 0,
) -> dict[str, object]:
    """Build a compact read-only dashboard summary."""

    _assert_dashboard_service_boundary()

    overview = build_dashboard_overview(
        references,
        insight_count=insight_count,
    )

    graph_summary = overview["graph_summary"]
    metrics = overview["metrics"]

    payload = {
        "dashboard": overview["dashboard"],
        "graph_summary": graph_summary,
        "metrics": metrics,
        "reference_count": overview["reference_count"],
        **_boundary_metadata(),
    }

    serialized = serialize_dashboard_payload(payload)
    ensure_dashboard_boundary(serialized)

    return serialized


def build_dashboard_status() -> dict[str, object]:
    """Return dashboard constitutional status only."""

    _assert_dashboard_service_boundary()

    payload = {
        "dashboard": dashboard_metadata(),
        "status": "ready",
        **_boundary_metadata(),
    }

    serialized = serialize_dashboard_payload(payload)
    ensure_dashboard_boundary(serialized)

    return serialized


def assert_dashboard_service_payload(
    payload: Mapping[str, object],
) -> None:
    """Fail closed if a dashboard service payload violates boundaries."""

    try:
        ensure_dashboard_boundary(payload)
    except AFRIPowerDashboardSerializationError as exc:
        raise AFRIPowerDashboardServiceError(str(exc)) from exc

    if payload.get("creates_authority") is not False:
        raise AFRIPowerDashboardServiceError(
            "dashboard service payload creates authority"
        )

    if payload.get("validates_truth") is not False:
        raise AFRIPowerDashboardServiceError(
            "dashboard service payload validates truth"
        )

    if payload.get("executes_runtime") is not False:
        raise AFRIPowerDashboardServiceError(
            "dashboard service payload executes runtime"
        )


def build_dashboard_payload(
    references: Iterable[Mapping[str, object]],
    *,
    insight_count: int = 0,
) -> dict[str, object]:
    """
    Compatibility dashboard payload used by legacy tests.
    """

    _assert_dashboard_service_boundary()

    overview = build_dashboard_summary(
        references,
        insight_count=insight_count,
    )

    payload = {
        **overview,
        "dashboard_status": "ready",
        "observational_only": True,
        "authoritative": False,
    }

    assert_dashboard_service_payload(payload)

    return payload

__all__ = [
    "AFRIPowerDashboardServiceError",
    "build_dashboard_overview",
    "build_dashboard_summary",
    "build_dashboard_status",
    "assert_dashboard_service_payload",
]
