"""Canonical event hashing."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
