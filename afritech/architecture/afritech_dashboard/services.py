"""Read-only AfriTech dashboard gateway services."""

from __future__ import annotations

from pathlib import Path

from afritech.architecture.config_loader import load_yaml_like


ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = ROOT / "afritech/architecture/integrations/dashboard_registry.yaml"
MENU_PATH = ROOT / "afritech/architecture/navigation/menu_config.yaml"
TEMPLATE_PATH = ROOT / "afritech/architecture/afritech_dashboard/templates/dashboard.html"

ROLE_SCOPES: dict[str, tuple[str, ...]] = {
    "admin": ("afriride", "afroprog", "afriprogramming"),
    "manager": ("afriride", "afroprog", "afriprogramming"),
    "operator": ("afriride", "afriprogramming"),
    "partner": ("afriride",),
    "auditor": ("afriride", "afriprogramming"),
    "user": ("afroprog",),
}

LIVE_DATA_ENDPOINTS: tuple[dict[str, str], ...] = (
    {
        "name": "System health",
        "path": "/system/health",
        "purpose": "Gateway heartbeat, enforcement mode, and service liveness.",
    },
    {
        "name": "Replay health",
        "path": "/system/replay/health",
        "purpose": "Replay success rate and failure count for trust state.",
    },
    {
        "name": "Evidence pipeline",
        "path": "/system/evidence",
        "purpose": "Receipts, trace coverage, and missing evidence signals.",
    },
    {
        "name": "Guard violations",
        "path": "/system/guards",
        "purpose": "Governance and runtime drift alerts surfaced to operators.",
    },
)


class AfriTechDashboardServiceError(RuntimeError):
    """Raised when the AfriTech dashboard gateway service is invalid."""


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
        "mutates_dashboard": False,
        "mutates_artifacts": False,
        "influences_runtime": False,
        "influences_replay": False,
        "influences_proof": False,
        "influences_ci": False,
        "influences_governance": False,
    }


def _read_yaml(path: Path) -> dict[str, object]:
    payload = load_yaml_like(path)
    if not isinstance(payload, dict):
        raise AfriTechDashboardServiceError(f"{path.name} must decode to a mapping")
    return payload


def _registry_entries() -> tuple[dict[str, object], ...]:
    payload = _read_yaml(REGISTRY_PATH)
    entries = payload.get("dashboards", ())
    if not isinstance(entries, list):
        raise AfriTechDashboardServiceError("dashboard registry must contain a list")
    normalized: list[dict[str, object]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise AfriTechDashboardServiceError("dashboard entries must be mappings")
        normalized.append(
            {
                "key": str(entry["key"]),
                "name": str(entry["name"]),
                "route": str(entry["route"]),
                "service": str(entry["service"]),
                "summary": str(entry["summary"]),
                "authority_mode": str(entry["authority_mode"]),
                "role_scope": tuple(str(role) for role in entry.get("role_scope", ())),
            }
        )
    return tuple(normalized)


def _menu_links() -> tuple[dict[str, object], ...]:
    payload = _read_yaml(MENU_PATH)
    main_dashboard = payload.get("main_dashboard")
    if not isinstance(main_dashboard, dict):
        raise AfriTechDashboardServiceError("menu config must expose main_dashboard")
    links = main_dashboard.get("links", ())
    if not isinstance(links, list):
        raise AfriTechDashboardServiceError("menu links must be a list")
    normalized: list[dict[str, object]] = []
    for link in links:
        if not isinstance(link, dict):
            raise AfriTechDashboardServiceError("menu link entries must be mappings")
        normalized.append(
            {
                "key": str(link["key"]),
                "name": str(link["name"]),
                "path": str(link["path"]),
                "icon": str(link["icon"]),
                "pillar": str(link["pillar"]),
            }
        )
    return tuple(normalized)


def _role_visible_dashboards(
    registry: tuple[dict[str, object], ...],
    role: str,
) -> tuple[dict[str, object], ...]:
    allowed = ROLE_SCOPES.get(role, ROLE_SCOPES["operator"])
    visible = [
        {
            "key": str(entry["key"]),
            "name": str(entry["name"]),
            "route": str(entry["route"]),
            "authority_mode": str(entry["authority_mode"]),
            "service": str(entry["service"]),
        }
        for entry in registry
        if entry["key"] != "afritech" and entry["key"] in allowed
    ]
    return tuple(visible)


def _deep_links(ride_id: str) -> tuple[dict[str, str], ...]:
    return (
        {
            "label": "Open replay",
            "path": f"/ride/{ride_id}/replay",
            "surface": "afriride",
        },
        {
            "label": "Open evidence",
            "path": f"/ride/{ride_id}/evidence",
            "surface": "afriride",
        },
        {
            "label": "Open proof certificate",
            "path": f"/trust/proof/{ride_id}",
            "surface": "afriprogramming",
        },
        {
            "label": "Open trust conversation",
            "path": "/trust/conversation",
            "surface": "afriprogramming",
        },
    )


def _cross_system_context(ride_id: str) -> dict[str, object]:
    return {
        "context_id": ride_id,
        "primary_entity": "ride",
        "surfaces": (
            {
                "system": "AfriRide",
                "focus": "execution_state",
                "path": f"/ride/{ride_id}/replay",
            },
            {
                "system": "AfroProg",
                "focus": "proposal_context",
                "path": "/afroprog/dashboard/",
            },
            {
                "system": "AfriProgramming",
                "focus": "governance_and_proof",
                "path": f"/trust/proof/{ride_id}",
            },
        ),
        "summary": (
            "View the same operational story across execution, productivity, and "
            "governed engineering without merging their authority boundaries."
        ),
    }


def build_dashboard_gateway_overview(
    *,
    role: str = "operator",
    ride_id: str = "ride-demo-001",
) -> dict[str, object]:
    """Build a read-only AfriTech dashboard gateway payload."""

    registry = _registry_entries()
    links = _menu_links()
    visible_dashboards = _role_visible_dashboards(registry, role)
    overview = {
        "dashboard": {
            "title": "AfriTech Dashboard",
            "route": "/afritech/dashboard/",
            "template": str(TEMPLATE_PATH.relative_to(ROOT)),
            "classification": "gateway_read_only",
            "cross_platform_analytics": True,
            "role_based_access": True,
        },
        "registry": registry,
        "menu": {
            "title": "AfriTech Dashboard",
            "links": links,
        },
        "role_surface": {
            "active_role": role,
            "visible_dashboards": visible_dashboards,
        },
        "live_data_wiring": LIVE_DATA_ENDPOINTS,
        "deep_links": _deep_links(ride_id),
        "cross_system_context": _cross_system_context(ride_id),
        "global_kpis": (
            {
                "label": "Linked dashboards",
                "value": len(registry) - 1,
                "detail": "AfriRide, AfroProg, and AfriProgramming are reachable from one gateway.",
            },
            {
                "label": "Services covered",
                "value": 3,
                "detail": "Mobility, freelance productivity, and engineering education remain separately bounded.",
            },
            {
                "label": "Authority mode",
                "value": "Gateway only",
                "detail": "The central dashboard navigates and observes. It does not create authority or truth.",
            },
        ),
        **_boundary_metadata(),
    }
    assert_gateway_payload(overview)
    return overview


def build_dashboard_gateway_status() -> dict[str, object]:
    payload = {
        "dashboard": {
            "title": "AfriTech Dashboard",
            "route": "/afritech/dashboard/",
        },
        "status": "ready",
        **_boundary_metadata(),
    }
    assert_gateway_payload(payload)
    return payload


def assert_gateway_payload(payload: dict[str, object]) -> None:
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
            raise AfriTechDashboardServiceError(f"gateway field must be true: {key}")
    for key in required_false:
        if payload.get(key) is not False:
            raise AfriTechDashboardServiceError(f"gateway field must be false: {key}")


__all__ = [
    "AfriTechDashboardServiceError",
    "assert_gateway_payload",
    "build_dashboard_gateway_overview",
    "build_dashboard_gateway_status",
]
