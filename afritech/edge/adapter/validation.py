"""Validation helpers for edge adapter envelopes."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def validate_adapted_request(adapted_input: Mapping[str, Any]) -> None:
    """Validate the deterministic envelope produced by the edge adapter."""

    if not isinstance(adapted_input.get("request_id"), str):
        raise ValueError("Adapted request_id must be a string")

    if not isinstance(adapted_input.get("timestamp"), int):
        raise ValueError("Adapted timestamp must be an integer")

    if not isinstance(adapted_input.get("payload"), Mapping):
        raise ValueError("Adapted payload must be a mapping")

