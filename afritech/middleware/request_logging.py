"""Structured JSON request logging for the FastAPI runtime."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp


LOGGER = logging.getLogger("afritech.request")
EXCLUDED_PATHS = {"/health", "/live", "/ready"}


class JsonRequestLoggingMiddleware(BaseHTTPMiddleware):
    """Emit one JSON log line per request with latency and request identity."""

    def __init__(self, app: ASGIApp, *, service: str = "afritech-api") -> None:
        super().__init__(app)
        self.service = service
        self.environment = os.environ.get("AFRITECH_RUNTIME_ENVIRONMENT", "PUBLIC_PILOT")

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = str(request.headers.get("X-Forwarded-For") or "").strip()
        if forwarded:
            return forwarded.split(",")[0].strip()
        client = request.client
        if client and client.host:
            return client.host
        return "unknown"

    @staticmethod
    def _request_id(request: Request) -> str:
        header_value = str(request.headers.get("X-Request-ID") or "").strip()
        if header_value:
            return header_value
        return uuid.uuid4().hex

    @staticmethod
    def _trace_context(request: Request) -> tuple[str, str, str]:
        traceparent = str(request.headers.get("traceparent") or "").strip()
        if traceparent:
            parts = traceparent.split("-")
            if len(parts) >= 4 and len(parts[1]) == 32 and len(parts[2]) == 16:
                trace_id = parts[1].lower()
                parent_span_id = parts[2].lower()
                span_id = uuid.uuid4().hex[:16]
                return trace_id, span_id, parent_span_id

        trace_id = uuid.uuid4().hex
        span_id = uuid.uuid4().hex[:16]
        parent_span_id = "0" * 16
        return trace_id, span_id, parent_span_id

    async def dispatch(self, request: Request, call_next):
        request_id = self._request_id(request)
        trace_id, span_id, parent_span_id = self._trace_context(request)
        request.state.request_id = request_id
        request.state.client_ip = self._client_ip(request)
        request.state.trace_id = trace_id
        request.state.span_id = span_id
        request.state.parent_span_id = parent_span_id
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            self._emit(
                request=request,
                request_id=request_id,
                client_ip=request.state.client_ip,
                trace_id=trace_id,
                span_id=span_id,
                status_code=500,
                duration_ms=duration_ms,
                level="ERROR",
            )
            raise

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        level = "DEBUG" if request.url.path in EXCLUDED_PATHS else "INFO"
        self._emit(
            request=request,
            request_id=request_id,
            client_ip=request.state.client_ip,
            trace_id=trace_id,
            span_id=span_id,
            status_code=response.status_code,
            duration_ms=duration_ms,
            level=level,
        )
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-Id"] = trace_id
        response.headers["X-Span-Id"] = span_id
        response.headers["traceparent"] = f"00-{trace_id}-{span_id}-01"
        return response

    def _emit(
        self,
        *,
        request: Request,
        request_id: str,
        client_ip: str,
        trace_id: str,
        span_id: str,
        status_code: int,
        duration_ms: float,
        level: str,
    ) -> None:
        record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": self.service,
            "environment": self.environment,
            "level": level,
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "request_id": request_id,
            "client_ip": client_ip,
            "trace_id": trace_id,
            "span_id": span_id,
        }
        message = json.dumps(record, separators=(",", ":"), sort_keys=True)
        if level == "DEBUG":
            LOGGER.debug(message)
        elif level == "ERROR":
            LOGGER.error(message)
        else:
            LOGGER.info(message)


__all__ = ["JsonRequestLoggingMiddleware"]
