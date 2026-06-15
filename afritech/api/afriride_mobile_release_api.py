"""Public AfriRide mobile release readiness API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

from afritech.afriride_mobile_release import build_afriride_mobile_release_readiness


def _json_object(payload: dict[str, Any]) -> dict[str, Any]:
    encoded = jsonable_encoder(payload)
    if not isinstance(encoded, dict):
        raise RuntimeError("mobile release payload must encode to JSON object")
    return encoded


def build_afriride_mobile_release_router() -> APIRouter:
    router = APIRouter(tags=["afriride-mobile-release"])

    @router.get("/public/afriride/mobile/release-readiness")
    def public_afriride_mobile_release_readiness() -> dict[str, Any]:
        return _json_object(build_afriride_mobile_release_readiness())

    return router


__all__ = ["build_afriride_mobile_release_router"]
