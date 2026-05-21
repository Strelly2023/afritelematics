"""Replay-stable normalization for edge-adapted inputs."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from typing import Any


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def stable_payload_hash(payload: Mapping[str, Any]) -> str:
    """Return a deterministic hash for a JSON-compatible payload mapping."""

    canonical_payload = _canonical_json(dict(payload))
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def normalize_input(adapted_input: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize an adapted edge input into a replay-stable canonical form."""

    payload = adapted_input.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("Normalized edge input requires mapping payload")

    timestamp = int(adapted_input["timestamp"])

    normalized = {
        "request_id": str(adapted_input["request_id"]),
        "payload_hash": stable_payload_hash(payload),
        "timestamp_bucket": timestamp // 1000,
    }

    if "user_id" in adapted_input:
        normalized["user_id"] = str(adapted_input["user_id"])

    for routing_key in ("city_id", "trip_id"):
        value = payload.get(routing_key)
        if value is not None:
            normalized[routing_key] = str(value)

    driver_candidates = payload.get("driver_candidates")
    if driver_candidates is not None:
        if not isinstance(driver_candidates, list):
            raise ValueError("driver_candidates must be a list")
        normalized["driver_candidates"] = deepcopy(driver_candidates)

    return normalized
