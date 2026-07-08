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

    async def dispatch(self, request: Request, call_next):
        request_id = self._request_id(request)
        request.state.request_id = request_id
        request.state.client_ip = self._client_ip(request)
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            self._emit(
                request=request,
                request_id=request_id,
                client_ip=request.state.client_ip,
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
            status_code=response.status_code,
            duration_ms=duration_ms,
            level=level,
        )
        response.headers["X-Request-ID"] = request_id
        return response

    def _emit(
        self,
        *,
        request: Request,
        request_id: str,
        client_ip: str,
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
        }
        message = json.dumps(record, separators=(",", ":"), sort_keys=True)
        if level == "DEBUG":
            LOGGER.debug(message)
        elif level == "ERROR":
            LOGGER.error(message)
        else:
            LOGGER.info(message)


__all__ = ["JsonRequestLoggingMiddleware"]
