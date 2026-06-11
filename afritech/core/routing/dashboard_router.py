"""Deterministic dashboard routing for the AfriTech gateway."""

from __future__ import annotations

from pathlib import Path

from afritech.architecture.config_loader import load_yaml_like


ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = ROOT / "afritech/architecture/integrations/dashboard_registry.yaml"
DEFAULT_ROUTE = "/afritech/dashboard/"


def _load_registry() -> dict[str, object]:
    payload = load_yaml_like(REGISTRY_PATH)
    if not isinstance(payload, dict):
        raise RuntimeError("dashboard registry must decode to a mapping")
    return payload


def dashboard_routes() -> dict[str, str]:
    payload = _load_registry()
    dashboards = payload.get("dashboards", ())
    routes: dict[str, str] = {}
    for entry in dashboards:
        if not isinstance(entry, dict):
            raise RuntimeError("dashboard registry entries must be mappings")
        key = str(entry.get("key", "")).strip()
        route = str(entry.get("route", "")).strip()
        if key and route:
            routes[key] = route
    if "afritech" not in routes:
        routes["afritech"] = DEFAULT_ROUTE
    return routes


def redirect_to_dashboard(app_name: str) -> str:
    """Return the deterministic route for a known dashboard key."""

    routes = dashboard_routes()
    return routes.get(app_name, DEFAULT_ROUTE)


__all__ = [
    "DEFAULT_ROUTE",
    "dashboard_routes",
    "redirect_to_dashboard",
]
