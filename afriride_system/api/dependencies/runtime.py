"""Runtime dependency providers for the AfriRide API layer."""

from __future__ import annotations

import os
from functools import lru_cache

from afriride_system.api.idempotency import (
    configure_idempotency_repository,
    reset_idempotency_store,
)
from afriride_system.backend.api_gateway.gateway import AfriRideGateway, build_gateway
from afriride_system.backend.trace_enforcement import TraceEventLog, build_trace_log


def _gateway_locator() -> str | None:
    return os.environ.get("AFRIRIDE_DATABASE_URL") or os.environ.get("AFRIRIDE_DB_PATH")


@lru_cache(maxsize=1)
def _cached_gateway(locator: str | None) -> AfriRideGateway:
    return build_gateway(db_path=locator, reset=False)


@lru_cache(maxsize=1)
def get_gateway() -> AfriRideGateway:
    gateway = _cached_gateway(_gateway_locator())
    configure_idempotency_repository(gateway.idempotency_repository)
    return gateway


def reset_gateway() -> AfriRideGateway:
    locator = _gateway_locator()
    build_gateway(db_path=locator, reset=True)
    _cached_gateway.cache_clear()
    get_gateway.cache_clear()
    gateway = _cached_gateway(locator)
    configure_idempotency_repository(gateway.idempotency_repository)
    reset_idempotency_store()
    return gateway


@lru_cache(maxsize=1)
def get_trace_log() -> TraceEventLog:
    return build_trace_log(db_path=_gateway_locator())


def reset_trace_log() -> TraceEventLog:
    trace_log = get_trace_log()
    trace_log.clear()
    get_trace_log.cache_clear()
    return get_trace_log()
