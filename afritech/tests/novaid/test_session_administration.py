from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from afritech.novaid.application.sessions import SessionAdministrationService


class _Row(dict):
    pass


class _SessionsRepo:
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str, str], _Row] = {}
        self.calls = defaultdict(int)

    def list_for_identity(self, tenant_id: str, identity_id: str) -> list[dict[str, object]]:
        self.calls["list_for_identity"] += 1
        return [
            {"session_id": session_id, **row}
            for (tenant, identity, session_id), row in self.rows.items()
            if tenant == tenant_id and identity == identity_id
        ]

    def get_for_identity(self, tenant_id: str, identity_id: str, session_id: str) -> dict[str, object] | None:
        self.calls["get_for_identity"] += 1
        return self.rows.get((tenant_id, identity_id, session_id))

    def revoke(self, tenant_id: str, identity_id: str, session_id: str, reason: str) -> int:
        self.calls["revoke"] += 1
        row = self.rows.get((tenant_id, identity_id, session_id))
        if row is None:
            return 0
        row["status"] = "REVOKED"
        row["revocation_reason"] = reason
        return 1

    def revoke_all_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> list[dict[str, object]]:
        self.calls["revoke_all_for_identity"] += 1
        revoked = []
        for (tenant, identity, session_id), row in list(self.rows.items()):
            if tenant != tenant_id or identity != identity_id:
                continue
            if row["status"] in {"REVOKED", "EXPIRED"}:
                continue
            row["status"] = "REVOKED"
            row["revocation_reason"] = reason
            revoked.append({"session_id": session_id, **row})
        return revoked

    def revoke_sessions_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> list[dict[str, object]]:
        self.calls["revoke_sessions_for_identity"] += 1
        return self.revoke_all_for_identity(tenant_id, identity_id, reason)

    def touch(self, tenant_id: str, identity_id: str, session_id: str, *, now: str) -> int:
        self.calls["touch"] += 1
        row = self.rows.get((tenant_id, identity_id, session_id))
        if row is None or row["status"] != "ACTIVE":
            return 0
        row["last_seen_at"] = now
        row["idle_expires_at"] = "2099-01-01T00:30:00+00:00"
        return 1

    def require_step_up(self, tenant_id: str, identity_id: str, session_id: str, *, until: str) -> int:
        self.calls["require_step_up"] += 1
        row = self.rows.get((tenant_id, identity_id, session_id))
        if row is None or row["status"] != "ACTIVE":
            return 0
        row["status"] = "STEP_UP_REQUIRED"
        row["step_up_expires_at"] = until
        return 1

    def complete_step_up(self, tenant_id: str, identity_id: str, session_id: str) -> int:
        self.calls["complete_step_up"] += 1
        row = self.rows.get((tenant_id, identity_id, session_id))
        if row is None or row["status"] != "STEP_UP_REQUIRED":
            return 0
        row["status"] = "ACTIVE"
        row["step_up_expires_at"] = None
        row["authentication_strength"] = "PASSWORD_OTP"
        return 1

    def lock_session(self, tenant_id: str, identity_id: str, session_id: str, *, locked_at: str) -> int:
        self.calls["lock_session"] += 1
        row = self.rows.get((tenant_id, identity_id, session_id))
        if row is None or row["status"] not in {"ACTIVE", "STEP_UP_REQUIRED"}:
            return 0
        row["status"] = "LOCKED"
        row["locked_at"] = locked_at
        return 1

    def unlock_session(self, tenant_id: str, identity_id: str, session_id: str) -> int:
        self.calls["unlock_session"] += 1
        row = self.rows.get((tenant_id, identity_id, session_id))
        if row is None or row["status"] != "LOCKED":
            return 0
        row["status"] = "ACTIVE"
        row["locked_at"] = None
        return 1

    def expire_stale(self, tenant_id: str, *, now: str) -> int:
        self.calls["expire_stale"] += 1
        expired = 0
        for (tenant, _, _), row in self.rows.items():
            if tenant != tenant_id:
                continue
            if row["status"] == "ACTIVE" and row["idle_expires_at"] <= now:
                row["status"] = "EXPIRED"
                expired += 1
        return expired

    def mark_compromised(self, tenant_id: str, identity_id: str, session_id: str, *, now: str):
        self.calls["mark_compromised"] += 1
        row = self.rows.get((tenant_id, identity_id, session_id))
        if row is None:
            return None
        row["status"] = "COMPROMISED"
        row["revoked_at"] = now
        row["compromised_at"] = now
        return row


class _Uow:
    def __init__(self) -> None:
        self.sessions = _SessionsRepo()
        self.bumped: list[tuple[str, str]] = []

    def __enter__(self) -> "_Uow":
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        return False

    def bump_identity_security_version(self, tenant_id: str, identity_id: str) -> None:
        self.bumped.append((tenant_id, identity_id))


class _Revocations:
    def __init__(self) -> None:
        self.revoked: list[tuple[str, str, datetime]] = []

    def revoke_session(self, tenant_id: str, session_id: str, expires_at: datetime) -> None:
        self.revoked.append((tenant_id, session_id, expires_at))


class _Outbox:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def enqueue(self, **kwargs) -> None:
        self.events.append(kwargs)


def _service() -> tuple[_Uow, _Revocations, _Outbox, SessionAdministrationService]:
    uow = _Uow()
    revocations = _Revocations()
    outbox = _Outbox()
    service = SessionAdministrationService(uow, revocations, outbox=outbox)
    return uow, revocations, outbox, service


def test_revoke_only_targets_the_selected_session() -> None:
    uow, revocations, outbox, service = _service()
    uow.sessions.rows[("tenant-1", "identity-1", "session-1")] = _Row(
        status="ACTIVE", expires_at="2099-01-01T00:00:00+00:00"
    )
    uow.sessions.rows[("tenant-1", "identity-1", "session-2")] = _Row(
        status="ACTIVE", expires_at="2099-01-01T00:00:00+00:00"
    )

    assert service.revoke("tenant-1", "identity-1", "session-1") is True
    assert uow.sessions.rows[("tenant-1", "identity-1", "session-1")]["status"] == "REVOKED"
    assert uow.sessions.rows[("tenant-1", "identity-1", "session-2")]["status"] == "ACTIVE"
    assert uow.sessions.calls["revoke_all_for_identity"] == 0
    assert len(outbox.events) == 1
    assert len(revocations.revoked) == 1


def test_logout_all_revokes_every_active_session_once() -> None:
    uow, revocations, outbox, service = _service()
    uow.sessions.rows[("tenant-1", "identity-1", "session-1")] = _Row(
        status="ACTIVE", expires_at="2099-01-01T00:00:00+00:00"
    )
    uow.sessions.rows[("tenant-1", "identity-1", "session-2")] = _Row(
        status="STEP_UP_REQUIRED", expires_at="2099-01-01T00:00:00+00:00"
    )

    assert service.logout_all("tenant-1", "identity-1") == 2
    assert uow.sessions.rows[("tenant-1", "identity-1", "session-1")]["status"] == "REVOKED"
    assert uow.sessions.rows[("tenant-1", "identity-1", "session-2")]["status"] == "REVOKED"
    assert uow.bumped == [("tenant-1", "identity-1")]
    assert len(outbox.events) == 1
    assert len(revocations.revoked) == 2


def test_mark_compromised_bumps_security_version_once() -> None:
    uow, revocations, outbox, service = _service()
    uow.sessions.rows[("tenant-1", "identity-1", "session-1")] = _Row(
        status="ACTIVE", expires_at="2099-01-01T00:00:00+00:00"
    )

    service.mark_compromised("tenant-1", "identity-1", "session-1")

    assert uow.sessions.rows[("tenant-1", "identity-1", "session-1")]["status"] == "COMPROMISED"
    assert uow.bumped == [("tenant-1", "identity-1")]
    assert len(outbox.events) == 1
    assert len(revocations.revoked) == 1
