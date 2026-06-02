"""FastAPI middleware for GA Elite trace envelope enforcement."""

from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from afriride_system.backend.trace_enforcement import TRACE_LOG, TraceEnvelopeError


RIDE_PATH_RE = re.compile(r"^/ride/([^/]+)/(accept|reject|start|complete)$")


async def trace_enforcement_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    body = await request.body()
    payload = _json_body(body)
    envelope = _extract_envelope(request, payload)

    if envelope is not None:
        try:
            event = TRACE_LOG.append(envelope, ride_id=_ride_id(request, payload))
        except TraceEnvelopeError as exc:
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
        response.headers["X-AfriRide-Trace-Sequence"] = str(request.state.trace_sequence_id)
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
        return envelope
    if request.method != "GET":
        return None
    if not _has_trace_headers(request):
        return None
    return {
        "event_id": request.headers.get("X-AfriRide-Event-Id"),
        "device_id": request.headers.get("X-AfriRide-Device-Id"),
        "actor_type": _actor_type_from_path(request.url.path),
        "actor_id": "operator",
        "action": f"{request.method} {request.url.path}",
        "payload": payload,
        "local_timestamp": request.headers.get("X-AfriRide-Client-Timestamp"),
        "app_version": request.headers.get("X-AfriRide-App-Version"),
        "test_mode": request.headers.get("X-AfriRide-Test-Mode") == "true",
    }


def _has_trace_headers(request: Request) -> bool:
    return all(
        request.headers.get(header)
        for header in (
            "X-AfriRide-Event-Id",
            "X-AfriRide-Device-Id",
            "X-AfriRide-Client-Timestamp",
            "X-AfriRide-App-Version",
        )
    )


def _is_instrumented_request(request: Request) -> bool:
    return request.headers.get("X-AfriRide-Test-Mode") == "true"


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
