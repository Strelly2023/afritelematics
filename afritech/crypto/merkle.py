"""Deterministic Merkle helpers for cross-system proof verification."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compute_merkle_root(logs: list[Any]) -> str:
    """Compute a deterministic SHA-256 Merkle root from proof logs."""

    if not isinstance(logs, list):
        raise ValueError("logs must be a list")
    if not logs:
        return _hash("[]")

    level = [_hash(_canonical_json(log)) for log in logs]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [
            _hash(level[index] + level[index + 1])
            for index in range(0, len(level), 2)
        ]
    return level[0]
