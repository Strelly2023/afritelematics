from __future__ import annotations

from datetime import UTC, datetime

from ..persistence import NovaIDUnitOfWork
from ..revocation import RevocationStore
from ..observability import NovaIDMetrics, NovaIDTracer
from ..outbox import RevocationOutbox


class SessionAdministrationService:
    def __init__(
        self,
        uow: NovaIDUnitOfWork,
        revocations: RevocationStore,
        *,
        outbox: RevocationOutbox | None = None,
        metrics: NovaIDMetrics | None = None,
        tracer: NovaIDTracer | None = None,
    ) -> None:
        self.uow, self.revocations = uow, revocations
        self.outbox = outbox or RevocationOutbox(uow)
        self.metrics, self.tracer = metrics or NovaIDMetrics(), tracer or NovaIDTracer()

    def list_own(self, tenant_id: str, identity_id: str) -> list[dict[str, object]]:
        return self.uow.sessions.list_for_identity(tenant_id, identity_id)

    def revoke(
        self, tenant_id: str, identity_id: str, session_id: str, reason: str = "USER_LOGOUT"
    ) -> bool:
        with self.uow:
            row = self.uow.sessions.get_for_identity(tenant_id, identity_id, session_id)
            if not row:
                raise LookupError("TENANT_ACCESS_DENIED")
            if row["status"] == "REVOKED":
                return False
            now = datetime.now(UTC).isoformat()
            self.uow.sessions.revoke(tenant_id, identity_id, session_id, reason)
            self.uow.sessions.revoke_all_for_identity(tenant_id, identity_id, reason)
            self.outbox.enqueue(
                tenant_id=tenant_id,
                event_type="SESSION_REVOKED",
                resource_type="SESSION",
                resource_id=session_id,
                event_version=1,
                payload={"reason": reason},
            )
        self.revocations.revoke_session(
            tenant_id, session_id, datetime.fromisoformat(row["expires_at"])
        )
        return True

    def logout_all(self, tenant_id: str, identity_id: str) -> int:
        with self.uow:
            rows = self.uow.sessions.revoke_sessions_for_identity(
                tenant_id, identity_id, "LOGOUT_ALL"
            )
            now = datetime.now(UTC).isoformat()
            identity = self.uow.sessions.get_for_identity(tenant_id, identity_id, session_id)
            if identity is not None:
                self.uow.bump_identity_security_version(tenant_id, identity_id)
            self.outbox.enqueue(
                tenant_id=tenant_id,
                event_type="ALL_SESSIONS_REVOKED",
                resource_type="IDENTITY",
                resource_id=identity_id,
                event_version=1,
                payload={"reason": "LOGOUT_ALL"},
            )
        for row in rows:
            self.revocations.revoke_session(
                tenant_id, row["session_id"], datetime.fromisoformat(row["expires_at"])
            )
        return len(rows)

    def touch(
        self, tenant_id: str, identity_id: str, session_id: str, *, now: datetime | None = None
    ) -> None:
        instant = now or datetime.now(UTC)
        with self.uow:
            if (
                self.uow.sessions.touch(
                    tenant_id, identity_id, session_id, now=instant.isoformat()
                )
                != 1
            ):
                raise LookupError("SESSION_NOT_ACTIVE")

    def require_step_up(
        self, tenant_id: str, identity_id: str, session_id: str, *, until: datetime
    ) -> None:
        with self.uow:
            if (
                self.uow.sessions.require_step_up(
                    tenant_id, identity_id, session_id, until=until.isoformat()
                )
                != 1
            ):
                raise LookupError("SESSION_NOT_ACTIVE")

    def complete_step_up(self, tenant_id: str, identity_id: str, session_id: str) -> None:
        with self.uow:
            if self.uow.sessions.complete_step_up(tenant_id, identity_id, session_id) != 1:
                raise LookupError("SESSION_STEP_UP_NOT_REQUIRED")

    def lock(self, tenant_id: str, identity_id: str, session_id: str) -> None:
        with self.uow:
            if (
                self.uow.sessions.lock_session(
                    tenant_id,
                    identity_id,
                    session_id,
                    locked_at=datetime.now(UTC).isoformat(),
                )
                != 1
            ):
                raise LookupError("SESSION_NOT_LOCKABLE")

    def unlock(self, tenant_id: str, identity_id: str, session_id: str) -> None:
        with self.uow:
            if self.uow.sessions.unlock_session(tenant_id, identity_id, session_id) != 1:
                raise LookupError("SESSION_NOT_LOCKED")

    def expire_stale(self, tenant_id: str, *, now: datetime | None = None) -> int:
        instant = now or datetime.now(UTC)
        expired = 0
        with self.tracer.span("novaid.session.expire", {"operation": "session.expire"}):
            with self.uow:
                expired += self.uow.sessions.expire_stale(tenant_id, now=instant.isoformat())
            self.metrics.increment("novaid_session_expiry_sweeps_total", outcome="success")
            for _ in range(expired):
                self.metrics.increment("novaid_sessions_expired_total", outcome="expired")
        return expired

    def mark_compromised(self, tenant_id: str, identity_id: str, session_id: str) -> None:
        with self.uow:
            row = self.uow.sessions.mark_compromised(
                tenant_id, identity_id, session_id, now=datetime.now(UTC).isoformat()
            )
            if not row:
                raise LookupError("TENANT_ACCESS_DENIED")
            identity = self.uow.sessions.get_for_identity(tenant_id, identity_id, session_id)
            if identity is not None:
                self.uow.bump_identity_security_version(tenant_id, identity_id)
            self.outbox.enqueue(
                tenant_id=tenant_id,
                event_type="SESSION_COMPROMISED",
                resource_type="SESSION",
                resource_id=session_id,
                event_version=1,
                payload={"reason": "SECURITY_CONTAINMENT"},
            )
        self.revocations.revoke_session(
            tenant_id, session_id, datetime.fromisoformat(row["expires_at"])
        )
        self.metrics.increment("novaid_sessions_compromised_total", outcome="contained")
