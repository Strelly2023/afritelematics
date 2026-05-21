"""Replay-safe event schema for the MVP production pipeline."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


def canonical_json(data: Mapping[str, Any]) -> str:
    """Serialize a mapping into replay-stable canonical JSON."""

    return json.dumps(dict(data), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class EventRecord:
    """Immutable replay ledger record for one deterministic execution."""

    request_id: str
    normalized_input: dict[str, Any]
    output: dict[str, Any]
    trace: dict[str, Any]
    replay_hash: str

    @staticmethod
    def generate_hash(data: Mapping[str, Any]) -> str:
        serialized = canonical_json(data)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

