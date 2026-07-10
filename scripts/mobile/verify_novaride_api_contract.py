#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from typing import Any

try:
    import certifi
except Exception:  # pragma: no cover - certifi is optional outside local dev.
    certifi = None


API_BASE_URL = os.environ.get("NOVARIDE_API_BASE_URL", "https://api.afritechnology.com").rstrip("/")
REQUIRED_DRIVER_ROUTES = {
    "/v1/driver/{driver_id}/availability": {"get"},
    "/v1/driver/{driver_id}/ride-queue": {"get"},
}


def fetch(path: str) -> tuple[int, bytes, str]:
    url = f"{API_BASE_URL}{path}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    cafile = certifi.where() if certifi else None
    with urllib.request.urlopen(request, timeout=12, context=ssl.create_default_context(cafile=cafile)) as response:
        return response.status, response.read(), response.headers.get("content-type", "")


def require_status(path: str, expected: int = 200) -> bytes:
    try:
      status, body, _ = fetch(path)
    except urllib.error.HTTPError as error:
      raise SystemExit(f"{path} returned HTTP {error.code}") from error
    except Exception as error:
      raise SystemExit(f"{path} failed: {error}") from error
    if status != expected:
        raise SystemExit(f"{path} returned HTTP {status}, expected {expected}")
    return body


def load_openapi() -> dict[str, Any]:
    body = require_status("/openapi.json")
    try:
        value = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as error:
        raise SystemExit("OpenAPI response is not valid JSON") from error
    if not isinstance(value, dict) or not isinstance(value.get("paths"), dict):
        raise SystemExit("OpenAPI response does not contain a paths object")
    return value


def verify_routes(openapi: dict[str, Any]) -> None:
    paths = openapi["paths"]
    failures: list[str] = []
    for route, methods in REQUIRED_DRIVER_ROUTES.items():
        definition = paths.get(route)
        if not isinstance(definition, dict):
            failures.append(f"missing route {route}")
            continue
        available = {method.lower() for method in definition}
        missing = methods - available
        if missing:
            failures.append(f"{route} missing methods {sorted(missing)}")
    if failures:
        raise SystemExit("; ".join(failures))


def main() -> int:
    require_status("/health")
    require_status("/live")
    require_status("/ready")
    verify_routes(load_openapi())
    print(json.dumps({"status": "ok", "api_base_url": API_BASE_URL, "routes": sorted(REQUIRED_DRIVER_ROUTES)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
