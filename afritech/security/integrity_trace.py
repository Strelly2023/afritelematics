from __future__ import annotations

import hashlib
import json
from typing import Any


class IntegrityTrace:
    @staticmethod
    def canonical_json(value: Any) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def hash_event(event: Any) -> str:
        encoded = IntegrityTrace.canonical_json(event)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @staticmethod
    def mutation_fingerprint(event: dict[str, Any]) -> str:
        return IntegrityTrace.hash_event(
            {
                "id": event["id"],
                "lineage": tuple(event.get("lineage", ())),
                "payload_hash": IntegrityTrace.hash_event(event["payload"]),
                "timestamp": event["timestamp"],
            }
        )
