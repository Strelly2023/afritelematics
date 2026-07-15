"""Redis-backed operational coordination abstractions.

Redis is used only for coordination and cache state. PostgreSQL remains
authoritative for ride, payment, sync, and evidence records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class KeyValueClient(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str, ex: int | None = None, nx: bool = False) -> bool: ...
    def delete(self, key: str) -> int: ...


@dataclass(slots=True)
class InMemoryKeyValueClient:
    values: dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str, ex: int | None = None, nx: bool = False) -> bool:
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    def delete(self, key: str) -> int:
        existed = key in self.values
        self.values.pop(key, None)
        return 1 if existed else 0


@dataclass(slots=True)
class RedisCoordinationService:
    client: KeyValueClient
    namespace: str = "novaride"

    def _key(self, *parts: str) -> str:
        return ":".join((self.namespace, *parts))

    def acquire_sync_lock(self, device_id: str, nonce: str, ttl_seconds: int = 300) -> bool:
        return self.client.set(self._key("sync-lock", device_id, nonce), "1", ex=ttl_seconds, nx=True)

    def suppress_duplicate(self, tenant_id: str, idempotency_key: str, ttl_seconds: int = 900) -> bool:
        return self.client.set(self._key("duplicate", tenant_id, idempotency_key), "1", ex=ttl_seconds, nx=True)

    def set_circuit_state(self, circuit: str, state: str, ttl_seconds: int = 3600) -> None:
        self.client.set(self._key("circuit", circuit), state, ex=ttl_seconds)

    def get_circuit_state(self, circuit: str) -> str | None:
        return self.client.get(self._key("circuit", circuit))

    def broadcast_emergency_mode(self, region: str, state: str, ttl_seconds: int = 3600) -> None:
        self.client.set(self._key("emergency-mode", region), state, ex=ttl_seconds)

    def region_degraded_mode(self, region: str) -> str | None:
        return self.client.get(self._key("emergency-mode", region))
