"""Deterministic edge adapter for external request envelopes."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


REQUIRED_FIELDS = ("request_id", "timestamp", "payload")


def adapt_request(raw_input: Mapping[str, Any]) -> dict[str, Any]:
    """Convert external request input into a canonical deterministic envelope."""

    missing = [field for field in REQUIRED_FIELDS if field not in raw_input]
    if missing:
        raise ValueError(f"Missing required edge input field: {missing[0]}")

    payload = raw_input["payload"]
    if not isinstance(payload, Mapping):
        raise ValueError("Edge input payload must be a mapping")

    return {
        "request_id": str(raw_input["request_id"]),
        "timestamp": int(raw_input["timestamp"]),
        "payload": deepcopy(dict(payload)),
    }

