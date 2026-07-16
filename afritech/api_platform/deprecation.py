"""Deprecation support for API endpoints."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeprecationRecord:
    endpoint_id: str
    deprecated_at: str
    sunset_at: str | None
    replacement: str | None
    reason: str = ""


def build_deprecation_headers(record: DeprecationRecord) -> dict[str, str]:
    headers = {"Deprecation": "true"}
    if record.sunset_at:
        headers["Sunset"] = record.sunset_at
    if record.replacement:
        headers["Link"] = f"<{record.replacement}>; rel=\"replacement\""
    return headers
