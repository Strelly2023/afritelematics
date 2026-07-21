from __future__ import annotations

from collections import defaultdict

import pytest

from afritech.novaid.application.authentication import AuthenticationError, DurableAuthenticationService


class _Uow:
    def __init__(self) -> None:
        self.refresh_tokens: dict[tuple[str, str], dict[str, object]] = {}
        self.calls = defaultdict(int)
        self.events: list[object] = []

    def __enter__(self) -> "_Uow":
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        return False

    def get_refresh_context(self, tenant_id: str, token_id: str):
        self.calls["get_refresh_context"] += 1
        return self.refresh_tokens.get((tenant_id, token_id))

    def mark_refresh_replayed(self, token_id: str) -> None:
        self.calls["mark_refresh_replayed"] += 1
        for row in self.refresh_tokens.values():
            if row["token_id"] == token_id:
                row["status"] = "REPLAYED"

    def revoke_refresh_family(self, family_id: str, *, now: str) -> None:
        self.calls["revoke_refresh_family"] += 1
        for row in self.refresh_tokens.values():
            if row["family_id"] == family_id:
                row["family_status"] = "REVOKED"

    def revoke_refresh_session(self, session_id: str, *, now: str, reason: str) -> None:
        self.calls["revoke_refresh_session"] += 1
        for row in self.refresh_tokens.values():
            if row["session_id"] == session_id:
                row["session_status"] = "REVOKED"

    def expire_refresh_session(self, tenant_id: str, session_id: str, *, now: str, reason: str) -> None:
        self.calls["expire_refresh_session"] += 1
        for row in self.refresh_tokens.values():
            if row["tenant_id"] == tenant_id and row["session_id"] == session_id:
                row["session_status"] = "EXPIRED"

    def mark_refresh_used(self, token_id: str, successor_id: str, *, now: str) -> int:
        self.calls["mark_refresh_used"] += 1
        for row in self.refresh_tokens.values():
            if row["token_id"] == token_id and row["status"] == "ACTIVE":
                row["status"] = "USED"
                row["replacement_token_id"] = successor_id
                return 1
        return 0

    def create_refresh_token(
        self,
        token_id: str,
        family_id: str,
        session_id: str,
        identity_id: str,
        tenant_id: str,
        token_hash: str,
        parent_token_id: str | None,
        *,
        issued_at: str,
        expires_at: str,
    ) -> None:
        self.calls["create_refresh_token"] += 1
        self.refresh_tokens[(tenant_id, token_id)] = {
            "token_id": token_id,
            "family_id": family_id,
            "session_id": session_id,
            "identity_id": identity_id,
            "tenant_id": tenant_id,
            "token_hash": token_hash,
            "parent_token_id": parent_token_id,
            "issued_at": issued_at,
            "expires_at": expires_at,
            "status": "ACTIVE",
            "family_status": "ACTIVE",
            "session_status": "ACTIVE",
            "idle_expires_at": expires_at,
            "absolute_expires_at": expires_at,
            "session_expires_at": expires_at,
        }

    def record_security_event(self, event) -> None:
        self.calls["record_security_event"] += 1
        self.events.append(event)


def _service(uow: _Uow) -> DurableAuthenticationService:
    return DurableAuthenticationService(uow, pepper=b"pepper-pepper-pepper-pepper-123456")


def test_refresh_rotates_token_and_persists_successor() -> None:
    uow = _Uow()
    service = _service(uow)
    raw = "refresh-token"
    token_id = "token-1"
    uow.refresh_tokens[("tenant-1", token_id)] = {
        "token_id": token_id,
        "family_id": "family-1",
        "session_id": "session-1",
        "identity_id": "identity-1",
        "tenant_id": "tenant-1",
        "token_hash": service._hash("refresh", raw),
        "parent_token_id": None,
        "issued_at": "2026-07-21T00:00:00+00:00",
        "expires_at": "2026-08-21T00:00:00+00:00",
        "status": "ACTIVE",
        "family_status": "ACTIVE",
        "session_status": "ACTIVE",
        "idle_expires_at": "2026-08-21T00:00:00+00:00",
        "absolute_expires_at": "2026-08-21T00:00:00+00:00",
        "session_expires_at": "2026-08-21T00:00:00+00:00",
    }

    replacement = service.refresh(
        tenant_id="tenant-1",
        presented_token=f"{token_id}.{raw}",
        correlation_id="correlation-1",
        request_id="request-1",
    )

    successor_id, successor_raw = replacement.split(".", 1)
    successor = uow.refresh_tokens[("tenant-1", successor_id)]
    assert successor["token_hash"] == service._hash("refresh", successor_raw)
    assert uow.refresh_tokens[("tenant-1", token_id)]["status"] == "USED"
    assert uow.calls["mark_refresh_used"] == 1
    assert uow.calls["create_refresh_token"] == 1
    assert uow.calls["record_security_event"] == 1
    assert len(uow.events) == 1


def test_refresh_replay_detects_and_revokes_family() -> None:
    uow = _Uow()
    service = _service(uow)
    raw = "refresh-token"
    token_id = "token-1"
    uow.refresh_tokens[("tenant-1", token_id)] = {
        "token_id": token_id,
        "family_id": "family-1",
        "session_id": "session-1",
        "identity_id": "identity-1",
        "tenant_id": "tenant-1",
        "token_hash": service._hash("refresh", raw),
        "parent_token_id": None,
        "issued_at": "2026-07-21T00:00:00+00:00",
        "expires_at": "2026-08-21T00:00:00+00:00",
        "status": "USED",
        "family_status": "ACTIVE",
        "session_status": "ACTIVE",
        "idle_expires_at": "2026-08-21T00:00:00+00:00",
        "absolute_expires_at": "2026-08-21T00:00:00+00:00",
        "session_expires_at": "2026-08-21T00:00:00+00:00",
    }

    with pytest.raises(AuthenticationError, match="TOKEN_REPLAY_DETECTED"):
        service.refresh(
            tenant_id="tenant-1",
            presented_token=f"{token_id}.{raw}",
            correlation_id="correlation-1",
            request_id="request-1",
        )

    assert uow.calls["mark_refresh_replayed"] == 1
    assert uow.calls["revoke_refresh_family"] == 1
    assert uow.calls["revoke_refresh_session"] == 1
    assert uow.calls["record_security_event"] == 1
    assert uow.refresh_tokens[("tenant-1", token_id)]["status"] == "REPLAYED"
    assert uow.refresh_tokens[("tenant-1", token_id)]["family_status"] == "REVOKED"
    assert uow.refresh_tokens[("tenant-1", token_id)]["session_status"] == "REVOKED"
