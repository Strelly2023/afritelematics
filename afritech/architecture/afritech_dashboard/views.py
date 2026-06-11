"""Read-only AfriTech dashboard gateway views."""

from __future__ import annotations

from afritech.architecture.afritech_dashboard.services import (
    AfriTechDashboardServiceError,
    assert_gateway_payload,
    build_dashboard_gateway_overview,
    build_dashboard_gateway_status,
)


class AfriTechDashboardViewError(RuntimeError):
    """Raised when the AfriTech dashboard gateway view violates its boundary."""


def _boundary_metadata() -> dict[str, object]:
    return {
        "read_only": True,
        "reference_only": True,
        "display_only": True,
        "projection_only": True,
        "gateway_only": True,
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


def render_dashboard_gateway_overview_view() -> dict[str, object]:
    payload = build_dashboard_gateway_overview()
    assert_gateway_payload(payload)
    rendered = {
        "view": "afritech_dashboard_gateway_overview",
        "payload": payload,
        **_boundary_metadata(),
    }
    return rendered


def render_dashboard_gateway_status_view() -> dict[str, object]:
    payload = build_dashboard_gateway_status()
    assert_gateway_payload(payload)
    rendered = {
        "view": "afritech_dashboard_gateway_status",
        "payload": payload,
        **_boundary_metadata(),
    }
    return rendered


def ensure_gateway_view_boundary(payload: dict[str, object]) -> None:
    required_true = (
        "read_only",
        "reference_only",
        "display_only",
        "projection_only",
        "gateway_only",
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
        if payload.get(key) is not True:
            raise AfriTechDashboardViewError(f"gateway view field must be true: {key}")
    for key in required_false:
        if payload.get(key) is not False:
            raise AfriTechDashboardViewError(f"gateway view field must be false: {key}")


__all__ = [
    "AfriTechDashboardViewError",
    "ensure_gateway_view_boundary",
    "render_dashboard_gateway_overview_view",
    "render_dashboard_gateway_status_view",
]
