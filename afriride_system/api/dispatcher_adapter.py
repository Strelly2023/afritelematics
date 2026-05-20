"""FastAPI dependency bridge to the Phase 1 command dispatcher."""

from __future__ import annotations

from afriride_system.backend.api_gateway.gateway import AfriRideGateway, build_gateway
from afriride_system.api.idempotency import reset_idempotency_store

_gateway = build_gateway()


def get_gateway() -> AfriRideGateway:
    return _gateway


def reset_gateway() -> AfriRideGateway:
    global _gateway
    _gateway = build_gateway()
    reset_idempotency_store()
    return _gateway
