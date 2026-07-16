"""API version helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApiVersionRecord:
    product_code: str
    version: str
    status: str
    created_at: str
    checksum: str
