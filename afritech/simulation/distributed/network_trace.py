from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class NetworkTrace:
    @staticmethod
    def hash_trace(trace: Any) -> str:
        encoded = canonical_json(trace)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @staticmethod
    def stable_int(value: Any) -> int:
        digest = NetworkTrace.hash_trace(value)
        return int(digest, 16)
