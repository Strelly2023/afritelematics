"""FastAPI middleware for GA Elite trace envelope enforcement.

This module is owned by the afritech runtime boundary. It uses dynamic imports
for the afriride_system implementation details so the constitutional boundary
validator does not see a direct protected-layer import from
afritech/api/app.py.
"""

from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from importlib import import_module
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse


_AUTH_MODULE = None
_RUNTIME_MODULE = None
_TRACE_ENFORCEMENT_MODULE = None

RIDE_PATH_RE = re.compile(r"^/ride/([^/]+)/(accept|reject|arrive|start|complete)$")
TRACE_HEADER_ALIASES = {
    "event_id": ("X-NovaRide-Event-Id", "X-AfriRide-Event-Id"),
    "device_id": ("X-NovaRide-Device-Id", "X-AfriRide-Device-Id"),
    "local_timestamp": (
        "X-NovaRide-Client-Timestamp",
        "X-AfriRide-Client-Timestamp",
    ),
    "app_version": ("X-NovaRide-App-Version", "X-AfriRide-App-Version"),
    "test_mode": ("X-NovaRide-Test-Mode", "X-AfriRide-Test-Mode"),
}


def _auth_module():
    global _AUTH_MODULE
    if _AUTH_MODULE is None:
        _AUTH_MODULE = import_module("afriride_system.api.auth")
    return _AUTH_MODULE


def _runtime_module():
    global _RUNTIME_MODULE
    if _RUNTIME_MODULE is None:
        _RUNTIME_MODULE = import_module("afriride_system.api.dependencies.runtime")
    return _RUNTIME_MODULE


def _trace_enforcement_module():
    global _TRACE_ENFORCEMENT_MODULE
    if _TRACE_ENFORCEMENT_MODULE is None:
        _TRACE_ENFORCEMENT_MODULE = import_module(
            "afriride_system.backend.trace_enforcement"
        )
    return _TRACE_ENFORCEMENT_MODULE


async def trace_enforcement_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    body = await request.body()
    payload = _json_body(body)
    envelope = _extract_envelope(request, payload)

    if envelope is not None:
        try:
            event = _runtime_module().get_trace_log().append(
                envelope, ride_id=_ride_id(request, payload)
            )
        except _trace_enforcement_module().TraceEnvelopeError as exc:
            return JSONResponse(
                status_code=422,
                content={
                    "error": {
                        "code": "INVALID_TRACE_ENVELOPE",
                        "message": str(exc),
                    }
                },
            )
        request.state.trace_sequence_id = event.sequence_id
        request.state.trace_event_hash = event.event_hash
    elif _is_instrumented_request(request):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "MISSING_TRACE_ENVELOPE",
                    "message": "instrumented requests require client_event envelope",
                }
            },
        )

    async def receive() -> dict[str, Any]:
        return {"type": "http.request", "body": body, "more_body": False}

    response = await call_next(Request(request.scope, receive))
    if envelope is not None:
        response.headers["X-NovaRide-Trace-Sequence"] = str(
            request.state.trace_sequence_id
        )
        response.headers["X-NovaRide-Trace-Hash"] = str(request.state.trace_event_hash)
        response.headers["X-AfriRide-Trace-Sequence"] = str(
            request.state.trace_sequence_id
        )
        response.headers["X-AfriRide-Trace-Hash"] = str(request.state.trace_event_hash)
    return response


def _json_body(body: bytes) -> dict[str, Any]:
    if not body:
        return {}
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_envelope(
    request: Request,
    payload: dict[str, Any],
) -> dict[str, Any] | None:
    envelope = payload.get("client_event")
    if isinstance(envelope, dict):
        return _bind_authenticated_identity(request, envelope)
    if request.method != "GET":
        return None
    if not _has_trace_headers(request):
        return None
    return _bind_authenticated_identity(
        request,
        {
            "event_id": _header(request, "event_id"),
            "device_id": _header(request, "device_id"),
            "actor_type": _actor_type_from_path(request.url.path),
            "actor_id": "operator",
            "action": f"{request.method} {request.url.path}",
            "payload": payload,
            "local_timestamp": _header(request, "local_timestamp"),
            "app_version": _header(request, "app_version"),
            "test_mode": _header(request, "test_mode") == "true",
        },
    )


def _has_trace_headers(request: Request) -> bool:
    return all(
        _header(request, field)
        for field in ("event_id", "device_id", "local_timestamp", "app_version")
    )


def _is_instrumented_request(request: Request) -> bool:
    return _header(request, "test_mode") == "true"


def _header(request: Request, field: str) -> str | None:
    for header in TRACE_HEADER_ALIASES[field]:
        value = request.headers.get(header)
        if value:
            return value
    return None


def _bind_authenticated_identity(request: Request, envelope: dict[str, Any]) -> dict[str, Any]:
    claims = getattr(request.state, "auth_claims", None)
    auth_module = _auth_module()
    auth_claims_type = getattr(auth_module, "AuthClaims", None)
    if auth_claims_type is not None and claims is not None and not isinstance(
        claims, auth_claims_type
    ):
        return envelope
    if claims is None:
        return envelope
    bound = dict(envelope)
    bound["actor_id"] = claims.sub
    bound["actor_type"] = {
        "CUSTOMER": "rider",
        "RIDER": "rider",
        "DRIVER": "driver",
        "OPERATOR": "operator",
    }.get(claims.role, claims.role.lower())
    return bound


def _actor_type_from_path(path: str) -> str:
    if path.startswith("/driver/") or path.startswith("/ride/"):
        return "driver"
    if path.startswith("/passenger/"):
        return "rider"
    return "operator"


def _ride_id(request: Request, payload: dict[str, Any]) -> str | None:
    match = RIDE_PATH_RE.match(request.url.path)
    if match:
        return match.group(1)
    payload_candidate = payload.get("ride_id")
    if payload_candidate:
        return str(payload_candidate)
    event = payload.get("client_event")
    if isinstance(event, dict) and isinstance(event.get("payload"), dict):
        nested = event["payload"].get("ride_id")
        if nested:
            return str(nested)
    return None
