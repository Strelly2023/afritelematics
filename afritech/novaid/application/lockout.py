from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from contextlib import nullcontext
import hashlib
import hmac

from ..persistence import NovaIDUnitOfWork


@dataclass(frozen=True)
class LockoutPolicy:
    threshold: int = 5
    observation_seconds: int = 900
    lock_seconds: int = 300


class AuthenticationLockoutService:
    def __init__(
        self, uow: NovaIDUnitOfWork, *, pepper: bytes, policy: LockoutPolicy | None = None
    ) -> None:
        self.uow, self.pepper = uow, pepper
        self.policy = policy or LockoutPolicy()

    def reference(self, identifier: str) -> str:
        return hmac.new(
            self.pepper, identifier.strip().lower().encode(), hashlib.sha256
        ).hexdigest()

    def is_locked(self, tenant_id: str, identifier: str) -> bool:
        row = self.uow.connection.execute(
            "SELECT locked_until FROM novaid_authentication_locks "
            "WHERE tenant_id=? AND identifier_hash=?",
            (tenant_id, self.reference(identifier)),
        ).fetchone()
        return bool(
            row
            and row["locked_until"]
            and datetime.fromisoformat(row["locked_until"]) > datetime.now(UTC)
        )

    def record_failure(self, tenant_id: str, identifier: str) -> bool:
        reference, now = self.reference(identifier), datetime.now(UTC)
        transaction = nullcontext() if self.uow.connection.in_transaction else self.uow
        with transaction:
            row = self.uow.connection.execute(
                "SELECT * FROM novaid_authentication_locks WHERE tenant_id=? AND identifier_hash=?",
                (tenant_id, reference),
            ).fetchone()
            reset = not row or datetime.fromisoformat(row["window_started_at"]) <= (
                now - timedelta(seconds=self.policy.observation_seconds)
            )
            count = 1 if reset else row["failure_count"] + 1
            locked_until = (
                (now + timedelta(seconds=self.policy.lock_seconds)).isoformat()
                if count >= self.policy.threshold
                else None
            )
            self.uow.connection.execute(
                "INSERT OR REPLACE INTO novaid_authentication_locks VALUES(?,?,?,?,?,?)",
                (
                    tenant_id,
                    reference,
                    count,
                    now.isoformat() if reset else row["window_started_at"],
                    locked_until,
                    now.isoformat(),
                ),
            )
        return locked_until is not None

    def reset(self, tenant_id: str, identifier: str) -> None:
        transaction = nullcontext() if self.uow.connection.in_transaction else self.uow
        with transaction:
            self.uow.connection.execute(
                "DELETE FROM novaid_authentication_locks WHERE tenant_id=? AND identifier_hash=?",
                (tenant_id, self.reference(identifier)),
            )
