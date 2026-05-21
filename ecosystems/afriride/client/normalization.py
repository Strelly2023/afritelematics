from __future__ import annotations

import hashlib
import json
from typing import Any

from ecosystems.afriride.client.device_model import MobileEvent


class EventNormalizer:
    def __init__(self, *, bucket_size: int = 1000) -> None:
        if bucket_size <= 0:
            raise ValueError("bucket_size must be positive")
        self.bucket_size = bucket_size

    def normalize(self, event: MobileEvent) -> dict[str, Any]:
        return {
            "device_id": str(event.device_id),
            "event_id": str(event.event_id),
            "timestamp": self._normalize_time(event.local_timestamp),
            "payload_hash": self._payload_hash(event.payload),
            "payload": event.payload,
        }

    def _normalize_time(self, timestamp: int) -> int:
        return int(timestamp) // self.bucket_size

    def _payload_hash(self, payload: dict[str, Any]) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()
