"""
AFRIPower dashboard views.

Views expose dashboard-ready read-only payloads.

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
)
from afritech.afripower.dashboard.services import (
    assert_dashboard_service_payload,
    build_dashboard_overview,
    build_dashboard_status,
    build_dashboard_summary,
)


class AFRIPowerDashboardViewError(RuntimeError):
    """Raised when dashboard view rendering fails."""


def _assert_dashboard_view_boundary() -> None:
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
        "mutates_view": False,
        "mutates_dashboard": False,
        "mutates_artifacts": False,
        "influences_runtime": False,
        "influences_replay": False,
        "influences_proof": False,
        "influences_ci": False,
        "influences_governance": False,
    }


def render_dashboard_overview_view(
    references: Iterable[Mapping[str, object]],
    *,
    insight_count: int = 0,
) -> dict[str, object]:
    """Render the full read-only AFRIPower dashboard overview view."""

    _assert_dashboard_view_boundary()

    payload = build_dashboard_overview(
        references,
        insight_count=insight_count,
    )
    assert_dashboard_service_payload(payload)

    rendered = {
        "view": "afripower_dashboard_overview",
        "payload": payload,
        **_boundary_metadata(),
    }

    return rendered


def render_dashboard_summary_view(
    references: Iterable[Mapping[str, object]],
    *,
    insight_count: int = 0,
) -> dict[str, object]:
    """Render the compact read-only AFRIPower dashboard summary view."""

    _assert_dashboard_view_boundary()

    payload = build_dashboard_summary(
        references,
        insight_count=insight_count,
    )
    assert_dashboard_service_payload(payload)

    rendered = {
        "view": "afripower_dashboard_summary",
        "payload": payload,
        **_boundary_metadata(),
    }

    return rendered


def render_dashboard_status_view() -> dict[str, object]:
    """Render the read-only AFRIPower dashboard status view."""

    _assert_dashboard_view_boundary()

    payload = build_dashboard_status()
    assert_dashboard_service_payload(payload)

    rendered = {
        "view": "afripower_dashboard_status",
        "payload": payload,
        **_boundary_metadata(),
    }

    return rendered


def ensure_dashboard_view_boundary(
    view_payload: Mapping[str, object],
) -> None:
    """Fail closed if a dashboard view violates AFRIPower boundaries."""

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
        "mutates_view",
        "mutates_dashboard",
        "mutates_artifacts",
        "influences_runtime",
        "influences_replay",
        "influences_proof",
        "influences_ci",
        "influences_governance",
    )

    for key in required_true:
        if view_payload.get(key) is not True:
            raise AFRIPowerDashboardViewError(
                f"dashboard view field must be true: {key}"
            )

    for key in required_false:
        if view_payload.get(key) is not False:
            raise AFRIPowerDashboardViewError(
                f"dashboard view field must be false: {key}"
            )


__all__ = [
    "AFRIPowerDashboardViewError",
    "render_dashboard_overview_view",
    "render_dashboard_summary_view",
    "render_dashboard_status_view",
    "ensure_dashboard_view_boundary",
]
