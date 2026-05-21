"""Validation helpers for normalized edge inputs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def validate_normalized_input(normalized_input: Mapping[str, Any]) -> None:
    """Validate normalized input before queue ingestion."""

    if not isinstance(normalized_input.get("request_id"), str):
        raise ValueError("Normalized request_id must be a string")

    payload_hash = normalized_input.get("payload_hash")
    if not isinstance(payload_hash, str) or len(payload_hash) != 64:
        raise ValueError("Normalized payload_hash must be a SHA-256 hex digest")

    if not isinstance(normalized_input.get("timestamp_bucket"), int):
        raise ValueError("Normalized timestamp_bucket must be an integer")

    if "user_id" in normalized_input and not isinstance(
        normalized_input.get("user_id"),
        str,
    ):
        raise ValueError("Normalized user_id must be a string")

    if "driver_candidates" in normalized_input and not isinstance(
        normalized_input.get("driver_candidates"),
        list,
    ):
        raise ValueError("Normalized driver_candidates must be a list")
