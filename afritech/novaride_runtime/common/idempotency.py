"""Idempotency primitives."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


def payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class IdempotencyRecord:
    tenant_id: str
    key: str
    command_hash: str
    result: dict[str, Any]
