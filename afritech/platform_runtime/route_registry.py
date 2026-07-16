"""Route registration and validation for executable NovaTech products."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from .errors import ProductRouteConflict
from .models import RoutePlan, RouteRegistration


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RouteRegistry:
    def __init__(self) -> None:
        self._routes: dict[tuple[str, str], RouteRegistration] = {}
        self._by_product: dict[str, list[RouteRegistration]] = {}

    def validate_product_routes(self, product_code: str, routers: tuple[APIRouter, ...]) -> tuple[RouteRegistration, ...]:
        registrations: list[RouteRegistration] = []
        for router in routers:
            for route in router.routes:
                path = getattr(route, "path", "")
                methods = tuple(sorted(m for m in getattr(route, "methods", set()) if m not in {"HEAD", "OPTIONS"}))
                operation_id = getattr(route, "operation_id", "") or f"{product_code}:{path}:{','.join(methods)}"
                registration = RouteRegistration(
                    product_code=product_code,
                    path=path,
                    methods=methods,
                    operation_id=operation_id,
                    authentication_required=not bool(getattr(route, "include_in_schema", True) and path.startswith("/public")),
                    permissions=(),
                    public=not getattr(route, "dependencies", None),
                    websocket=getattr(route, "path", "").startswith("/ws") or route.__class__.__name__.lower().startswith("websocket"),
                    timeout_seconds=30,
                )
                self.register(registration)
                registrations.append(registration)
        return tuple(registrations)

    def register(self, registration: RouteRegistration) -> None:
        key = (registration.path, ",".join(registration.methods))
        if any(registration.path.startswith(prefix) for prefix in ("/v1/platform", "/v1/identity", "/v1/governance", "/v1/audit", "/v1/evidence", "/v1/internal", "/health", "/metrics", "/docs", "/openapi.json")):
            raise ProductRouteConflict("protected_route_prefix")
        existing = self._routes.get(key)
        if existing and existing.product_code.lower() != registration.product_code.lower():
            raise ProductRouteConflict("duplicate_route")
        self._routes[key] = registration
        self._by_product.setdefault(registration.product_code.lower(), [])
        self._by_product[registration.product_code.lower()] = [
            route
            for route in self._by_product[registration.product_code.lower()]
            if not (route.path == registration.path and route.methods == registration.methods)
        ]
        self._by_product[registration.product_code.lower()].append(registration)

    def unregister_product(self, product_code: str) -> None:
        key = product_code.lower()
        routes = self._by_product.pop(key, [])
        for route in routes:
            self._routes.pop((route.path, ",".join(route.methods)), None)

    def list_product_routes(self, product_code: str) -> tuple[RouteRegistration, ...]:
        return tuple(self._by_product.get(product_code.lower(), []))

    def snapshot(self) -> dict[str, Any]:
        return {
            "routes": [
                {
                    "product_code": route.product_code,
                    "path": route.path,
                    "methods": list(route.methods),
                    "operation_id": route.operation_id,
                    "public": route.public,
                    "websocket": route.websocket,
                    "timeout_seconds": route.timeout_seconds,
                }
                for route in self._routes.values()
            ]
        }

    def plan(self, product_code: str, additions: tuple[RouteRegistration, ...] = (), removals: tuple[RouteRegistration, ...] = ()) -> RoutePlan:
        conflicts = []
        for route in additions:
            key = (route.path, ",".join(route.methods))
            existing = self._routes.get(key)
            if existing and existing.product_code.lower() != product_code.lower():
                conflicts.append(f"duplicate:{route.path}:{','.join(route.methods)}")
        return RoutePlan(
            revision_id=f"route-{product_code}-{datetime.now(timezone.utc).timestamp():.0f}",
            product_code=product_code,
            additions=additions,
            removals=removals,
            conflicts=tuple(conflicts),
            requires_restart=bool(additions or removals),
        )

    def validate_plan(self, plan: RoutePlan) -> None:
        if plan.conflicts:
            raise ProductRouteConflict(";".join(plan.conflicts))


__all__ = ["RouteRegistry"]
