from __future__ import annotations

import hashlib
import json
from typing import Any

from ecosystems.afriride.client.device_model import MobileEvent
from ecosystems.afriride.client.normalization import EventNormalizer
from ecosystems.afriride.client.sync_engine import SyncEngine


class ClientReplayEngine:
    def __init__(
        self,
        *,
        normalizer: EventNormalizer | None = None,
        sync_engine: SyncEngine | None = None,
    ) -> None:
        self.normalizer = normalizer or EventNormalizer()
        self.sync_engine = sync_engine or SyncEngine()

    def replay(self, events: list[MobileEvent]) -> tuple[dict[str, Any], ...]:
        normalized = [self.normalizer.normalize(event) for event in events]
        return self.sync_engine.reconcile(normalized)


def hash_client_trace(trace: tuple[dict[str, Any], ...]) -> str:
    payload = json.dumps(trace, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()
