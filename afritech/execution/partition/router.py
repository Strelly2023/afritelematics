"""Deterministic partition router for production pipeline admission."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any


ROUTING_KEYS = ("city_id", "trip_id", "request_id", "user_id")


def get_partition(event: Mapping[str, Any], num_partitions: int = 8) -> int:
    """Return a stable partition for an event using declared routing keys."""

    if num_partitions <= 0:
        raise ValueError("num_partitions must be positive")

    for key in ROUTING_KEYS:
        value = event.get(key)
        if value is not None:
            routing_value = f"{key}:{value}"
            break
    else:
        raise ValueError("Partition routing requires a declared routing key")

    digest = hashlib.sha256(routing_value.encode("utf-8")).hexdigest()
    return int(digest, 16) % num_partitions

