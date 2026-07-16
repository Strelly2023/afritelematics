from __future__ import annotations

import pytest
from fastapi import APIRouter

from afritech.platform_runtime.errors import ProductRouteConflict
from afritech.platform_runtime.route_registry import RouteRegistry


def test_product_cannot_mount_platform_prefix() -> None:
    registry = RouteRegistry()
    router = APIRouter()

    @router.get("/v1/platform/runtime")
    def _platform_route():
        return {"ok": True}

    with pytest.raises(ProductRouteConflict):
        registry.validate_product_routes("novafleet", (router,))


def test_product_route_conflict_is_rejected() -> None:
    registry = RouteRegistry()
    first = APIRouter()
    second = APIRouter()

    @first.get("/v1/novafleet/vehicles")
    def _first():
        return {"ok": True}

    @second.get("/v1/novafleet/vehicles")
    def _second():
        return {"ok": False}

    registry.validate_product_routes("novafleet", (first,))
    with pytest.raises(ProductRouteConflict):
        registry.validate_product_routes("novapay", (second,))
