"""Deterministic core execution entrypoint for the MVP edge pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from afritech.core.matching_engine import match_driver


def execute(normalized_input: Mapping[str, Any]) -> dict[str, Any]:
    """Execute a normalized input through deterministic core logic."""

    result = {
        "status": "processed",
        "request_id": str(normalized_input["request_id"]),
        "result": str(normalized_input["payload_hash"]),
    }

    if "user_id" in normalized_input:
        result["user_id"] = str(normalized_input["user_id"])

    drivers = normalized_input.get("driver_candidates")
    if drivers is not None:
        if not isinstance(drivers, list):
            raise ValueError("driver_candidates must be a list")
        result["matching"] = match_driver(normalized_input, drivers)

    return result
