from __future__ import annotations

from time import perf_counter
from typing import Any
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class DistributedTracingMiddleware(BaseHTTPMiddleware):
    """Attach correlation and trace identifiers to each request."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        trace_id = request.headers.get("x-trace-id") or uuid4().hex
        correlation_id = request.headers.get("x-correlation-id") or uuid4().hex
        service_name = getattr(getattr(request.app, "state", None), "service_definition", None)
        service_name_text = getattr(service_name, "name", None) or getattr(request.app.state, "service_name", None)
        request.state.trace_id = trace_id
        request.state.correlation_id = correlation_id
        request.state.service_name = service_name_text
        started = perf_counter()
        response = await call_next(request)
        response.headers.setdefault("x-trace-id", trace_id)
        response.headers.setdefault("x-correlation-id", correlation_id)
        if service_name_text:
            response.headers.setdefault("x-service-name", str(service_name_text))
        response.headers.setdefault("x-request-latency-ms", str(int(round((perf_counter() - started) * 1000))))
        return response


def tracing_context(request: Request) -> dict[str, Any]:
    return {
        "trace_id": getattr(request.state, "trace_id", None),
        "correlation_id": getattr(request.state, "correlation_id", None),
        "service_name": getattr(request.state, "service_name", None),
    }
