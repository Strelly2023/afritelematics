"""Runtime schema admission middleware for NovaRide contract payloads."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from afritech.platform_contracts.schema_registry import (
    SchemaRegistry,
    SchemaRegistryError,
    build_schema_registry,
)


class SchemaRegistryMiddleware(BaseHTTPMiddleware):
    """Validate governed event payloads before they reach runtime handlers."""

    def __init__(
        self,
        app: ASGIApp,
        *,
        registry: SchemaRegistry | None = None,
        protected_paths: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.registry = registry or build_schema_registry()
        self.protected_paths = tuple(protected_paths or (
            "/v1/contracts/events/publish",
            "/v1/contracts/events/validate",
        ))

    async def dispatch(self, request: Request, call_next):
        if request.method not in {"POST", "PUT", "PATCH"}:
            return await call_next(request)
        if not any(request.url.path.startswith(path) for path in self.protected_paths):
            return await call_next(request)

        body = await request.body()
        if not body:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "EMPTY_CONTRACT_REQUEST",
                        "message": "contract payload required",
                    }
                },
            )

        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "INVALID_JSON",
                        "message": "payload must be valid JSON",
                    }
                },
            )

        try:
            admission = self._validate_payload(payload)
        except SchemaRegistryError as exc:
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "code": "SCHEMA_CONTRACT_REJECTED",
                        "message": str(exc),
                    }
                },
            )

        request.state.novaride_contract_admission = admission
        return await call_next(request)

    def _validate_payload(self, payload: Any) -> dict[str, Any]:
        if isinstance(payload, Mapping):
            if isinstance(payload.get("events"), list):
                result = self.registry.validate_batch(_coerce_events(payload["events"]))
                return {
                    "mode": "batch",
                    "result": result,
                }
            if isinstance(payload.get("event"), Mapping):
                result = self.registry.validate_event(dict(payload["event"]))
                return {
                    "mode": "single",
                    "result": result,
                }
            if payload.get("event_type"):
                result = self.registry.validate_event(dict(payload))
                return {
                    "mode": "single",
                    "result": result,
                }
        raise SchemaRegistryError("event_or_events_required")


def _coerce_events(events: Iterable[Any]) -> list[dict[str, Any]]:
    coerced: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, Mapping):
            raise SchemaRegistryError("event_must_be_mapping")
        coerced.append(dict(event))
    if not coerced:
        raise SchemaRegistryError("event_or_events_required")
    return coerced


__all__ = ["SchemaRegistryMiddleware"]
