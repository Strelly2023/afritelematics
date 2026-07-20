from __future__ import annotations

from datetime import UTC, datetime, timedelta

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
        rows = self.uow.connection.execute(
            "SELECT session_id,status,authentication_strength,created_at,last_seen_at,expires_at,"
            "authenticated_at,idle_expires_at,absolute_expires_at,pending_mfa_expires_at,"
            "step_up_expires_at,device_reference "
            "FROM novaid_authentication_sessions WHERE tenant_id=? AND identity_id=? "
            "ORDER BY created_at DESC",
            (tenant_id, identity_id),
        ).fetchall()
        return [dict(row) for row in rows]

    def revoke(
        self, tenant_id: str, identity_id: str, session_id: str, reason: str = "USER_LOGOUT"
    ) -> bool:
        with self.uow:
            row = self.uow.connection.execute(
                "SELECT expires_at,status FROM novaid_authentication_sessions "
                "WHERE tenant_id=? AND identity_id=? AND session_id=?",
                (tenant_id, identity_id, session_id),
            ).fetchone()
            if not row:
                raise LookupError("TENANT_ACCESS_DENIED")
            if row["status"] == "REVOKED":
                return False
            now = datetime.now(UTC).isoformat()
            self.uow.connection.execute(
                "UPDATE novaid_authentication_sessions SET status='REVOKED',"
                "revoked_at=?,revocation_reason=? "
                "WHERE tenant_id=? AND identity_id=? AND session_id=?",
                (now, reason, tenant_id, identity_id, session_id),
            )
            self.uow.connection.execute(
                "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=? "
                "WHERE tenant_id=? AND identity_id=? AND session_id=? AND status='ACTIVE'",
                (now, tenant_id, identity_id, session_id),
            )
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
            rows = self.uow.connection.execute(
                "SELECT session_id,expires_at FROM novaid_authentication_sessions "
                "WHERE tenant_id=? AND identity_id=? AND status NOT IN ('REVOKED','EXPIRED')",
                (tenant_id, identity_id),
            ).fetchall()
            now = datetime.now(UTC).isoformat()
            self.uow.connection.execute(
                "UPDATE novaid_authentication_sessions SET status='REVOKED',revoked_at=?,"
                "revocation_reason='LOGOUT_ALL' WHERE tenant_id=? AND identity_id=? "
                "AND status NOT IN ('REVOKED','EXPIRED')",
                (now, tenant_id, identity_id),
            )
            self.uow.connection.execute(
                "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=? "
                "WHERE tenant_id=? AND identity_id=? AND status='ACTIVE'",
                (now, tenant_id, identity_id),
            )
            self.uow.connection.execute(
                "UPDATE novaid_identities SET security_version=security_version+1,"
                "version=version+1 "
                "WHERE tenant_id=? AND identity_id=?",
                (tenant_id, identity_id),
            )
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
            result = self.uow.connection.execute(
                "UPDATE novaid_authentication_sessions SET last_seen_at=?,idle_expires_at=? "
                "WHERE tenant_id=? AND identity_id=? AND session_id=? AND status='ACTIVE'",
                (
                    (instant).isoformat(),
                    (instant + timedelta(minutes=30)).isoformat(),
                    tenant_id,
                    identity_id,
                    session_id,
                ),
            )
            if result.rowcount != 1:
                raise LookupError("SESSION_NOT_ACTIVE")

    def require_step_up(
        self, tenant_id: str, identity_id: str, session_id: str, *, until: datetime
    ) -> None:
        with self.uow:
            result = self.uow.connection.execute(
                "UPDATE novaid_authentication_sessions SET status='STEP_UP_REQUIRED',"
                "step_up_expires_at=? WHERE tenant_id=? AND identity_id=? AND session_id=? "
                "AND status='ACTIVE'",
                (until.isoformat(), tenant_id, identity_id, session_id),
            )
            if result.rowcount != 1:
                raise LookupError("SESSION_NOT_ACTIVE")

    def complete_step_up(self, tenant_id: str, identity_id: str, session_id: str) -> None:
        with self.uow:
            result = self.uow.connection.execute(
                "UPDATE novaid_authentication_sessions SET status='ACTIVE',step_up_expires_at=NULL,"
                "authentication_strength='PASSWORD_OTP' WHERE tenant_id=? AND identity_id=? "
                "AND session_id=? AND status='STEP_UP_REQUIRED'",
                (tenant_id, identity_id, session_id),
            )
            if result.rowcount != 1:
                raise LookupError("SESSION_STEP_UP_NOT_REQUIRED")

    def lock(self, tenant_id: str, identity_id: str, session_id: str) -> None:
        with self.uow:
            result = self.uow.connection.execute(
                "UPDATE novaid_authentication_sessions SET status='LOCKED',locked_at=? "
                "WHERE tenant_id=? AND identity_id=? AND session_id=? "
                "AND status IN ('ACTIVE','STEP_UP_REQUIRED')",
                (datetime.now(UTC).isoformat(), tenant_id, identity_id, session_id),
            )
            if result.rowcount != 1:
                raise LookupError("SESSION_NOT_LOCKABLE")

    def unlock(self, tenant_id: str, identity_id: str, session_id: str) -> None:
        with self.uow:
            result = self.uow.connection.execute(
                "UPDATE novaid_authentication_sessions SET status='ACTIVE',locked_at=NULL "
                "WHERE tenant_id=? AND identity_id=? AND session_id=? AND status='LOCKED'",
                (tenant_id, identity_id, session_id),
            )
            if result.rowcount != 1:
                raise LookupError("SESSION_NOT_LOCKED")

    def expire_stale(self, tenant_id: str, *, now: datetime | None = None) -> int:
        instant = now or datetime.now(UTC)
        expired = 0
        with self.tracer.span("novaid.session.expire", {"operation": "session.expire"}):
            with self.uow:
                rules = (
                    ("PENDING_MFA", "pending_mfa_expires_at", "PENDING_MFA_EXPIRY"),
                    ("ACTIVE", "idle_expires_at", "IDLE_EXPIRY"),
                    ("STEP_UP_REQUIRED", "step_up_expires_at", "STEP_UP_EXPIRY"),
                )
                for status, column, reason in rules:
                    result = self.uow.connection.execute(
                        f"UPDATE novaid_authentication_sessions SET status='EXPIRED',expired_at=?,"
                        "revoked_at=?,revocation_reason=? WHERE tenant_id=? AND status=? "
                        f"AND {column} IS NOT NULL AND {column}<=?",
                        (
                            instant.isoformat(),
                            instant.isoformat(),
                            reason,
                            tenant_id,
                            status,
                            instant.isoformat(),
                        ),
                    )
                    expired += result.rowcount
                result = self.uow.connection.execute(
                    "UPDATE novaid_authentication_sessions SET status='EXPIRED',expired_at=?,"
                    "revoked_at=?,revocation_reason='ABSOLUTE_EXPIRY' WHERE tenant_id=? "
                    "AND status IN ('ACTIVE','PENDING_MFA','STEP_UP_REQUIRED','LOCKED') "
                    "AND COALESCE(absolute_expires_at,expires_at)<=?",
                    (instant.isoformat(), instant.isoformat(), tenant_id, instant.isoformat()),
                )
                expired += result.rowcount
            self.metrics.increment("novaid_session_expiry_sweeps_total", outcome="success")
            for _ in range(expired):
                self.metrics.increment("novaid_sessions_expired_total", outcome="expired")
        return expired

    def mark_compromised(self, tenant_id: str, identity_id: str, session_id: str) -> None:
        with self.uow:
            row = self.uow.connection.execute(
                "SELECT expires_at FROM novaid_authentication_sessions "
                "WHERE tenant_id=? AND identity_id=? AND session_id=?",
                (tenant_id, identity_id, session_id),
            ).fetchone()
            if not row:
                raise LookupError("TENANT_ACCESS_DENIED")
            now = datetime.now(UTC).isoformat()
            self.uow.connection.execute(
                "UPDATE novaid_authentication_sessions SET status='COMPROMISED',"
                "revoked_at=?,compromised_at=?,revocation_reason='SECURITY_CONTAINMENT',"
                "compromise_reason='SECURITY_CONTAINMENT' WHERE tenant_id=? AND identity_id=? "
                "AND session_id=? AND status NOT IN ('COMPROMISED','REVOKED','EXPIRED')",
                (now, now, tenant_id, identity_id, session_id),
            )
            self.uow.connection.execute(
                "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=? "
                "WHERE tenant_id=? AND session_id=? AND status='ACTIVE'",
                (now, tenant_id, session_id),
            )
            self.uow.connection.execute(
                "UPDATE novaid_identities SET security_version=security_version+1,"
                "version=version+1 "
                "WHERE tenant_id=? AND identity_id=?",
                (tenant_id, identity_id),
            )
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
