from __future__ import annotations

from datetime import UTC, datetime
from threading import RLock
from typing import Protocol


class RevocationStore(Protocol):
    def revoke_session(self, tenant_id: str, session_id: str, expires_at: datetime) -> None: ...
    def revoke_family(self, tenant_id: str, family_id: str, expires_at: datetime) -> None: ...
    def is_session_revoked(self, tenant_id: str, session_id: str) -> bool: ...
    def is_family_revoked(self, tenant_id: str, family_id: str) -> bool: ...


class ProcessLocalRevocationStore:
    """Deterministic test adapter; not a multi-instance certification."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, str, str], datetime] = {}
        self._lock = RLock()

    def _revoke(self, kind: str, tenant: str, identifier: str, expiry: datetime) -> None:
        if expiry.tzinfo is None:
            raise ValueError("timezone_required")
        with self._lock:
            self._items[(kind, tenant, identifier)] = expiry

    def revoke_session(self, tenant_id: str, session_id: str, expires_at: datetime) -> None:
        self._revoke("session", tenant_id, session_id, expires_at)

    def revoke_family(self, tenant_id: str, family_id: str, expires_at: datetime) -> None:
        self._revoke("family", tenant_id, family_id, expires_at)

    def _is_revoked(self, kind: str, tenant: str, identifier: str) -> bool:
        with self._lock:
            expiry = self._items.get((kind, tenant, identifier))
            if expiry and expiry > datetime.now(UTC):
                return True
            if expiry:
                del self._items[(kind, tenant, identifier)]
            return False

    def is_session_revoked(self, tenant_id: str, session_id: str) -> bool:
        return self._is_revoked("session", tenant_id, session_id)

    def is_family_revoked(self, tenant_id: str, family_id: str) -> bool:
        return self._is_revoked("family", tenant_id, family_id)


class RedisRevocationStore:
    """Redis fast-path adapter; durable database state remains authoritative."""

    def __init__(self, client) -> None:
        self.client = client

    def _key(self, kind: str, tenant: str, identifier: str) -> str:
        return f"novaid:revoked:{tenant}:{kind}:{identifier}"

    def _revoke(self, kind: str, tenant: str, identifier: str, expiry: datetime) -> None:
        ttl = max(1, int((expiry - datetime.now(UTC)).total_seconds()))
        self.client.set(self._key(kind, tenant, identifier), "1", ex=ttl)
        self.client.publish("novaid:revocations", f"{tenant}:{kind}:{identifier}")

    def revoke_session(self, tenant_id: str, session_id: str, expires_at: datetime) -> None:
        self._revoke("session", tenant_id, session_id, expires_at)

    def revoke_family(self, tenant_id: str, family_id: str, expires_at: datetime) -> None:
        self._revoke("family", tenant_id, family_id, expires_at)

    def is_session_revoked(self, tenant_id: str, session_id: str) -> bool:
        return bool(self.client.get(self._key("session", tenant_id, session_id)))

    def is_family_revoked(self, tenant_id: str, family_id: str) -> bool:
        return bool(self.client.get(self._key("family", tenant_id, family_id)))
