"""Cache helpers for integration responses."""

from __future__ import annotations

from dataclasses import dataclass
from time import time

from .contracts import CachePolicy


@dataclass(slots=True)
class CacheEntry:
    value: object
    expires_at: float
    policy_id: str
    tenant_id: str | None
    user_id: str | None


class IntegrationCache:
    def __init__(self) -> None:
        self._entries: dict[str, CacheEntry] = {}

    def get(self, key: str) -> object | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at < time():
            self._entries.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: object, policy: CachePolicy, *, tenant_id: str | None = None, user_id: str | None = None) -> None:
        self._entries[key] = CacheEntry(
            value=value,
            expires_at=time() + max(0, policy.ttl_seconds),
            policy_id=policy.policy_id,
            tenant_id=tenant_id if policy.tenant_scoped else None,
            user_id=user_id if policy.user_scoped else None,
        )

    def invalidate(self, prefix: str) -> None:
        for key in [key for key in self._entries if key.startswith(prefix)]:
            self._entries.pop(key, None)
