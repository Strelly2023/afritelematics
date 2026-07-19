"""Security-specific persistence contracts shared by SQLite and PostgreSQL adapters."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class Result(Protocol):
    rowcount: int

    def fetchone(self) -> Any | None: ...

    def fetchall(self) -> list[Any]: ...


class Connection(Protocol):
    def execute(self, statement: str, parameters: tuple[Any, ...] = ()) -> Result: ...


class TenantRepository(Protocol):
    def get_active(self, tenant_id: str) -> Any | None: ...


class IdentityRepository(Protocol):
    def get_for_tenant(
        self, tenant_id: str, identity_id: str, *, lock: bool = False
    ) -> Any | None: ...

    def increment_security_version(
        self, tenant_id: str, identity_id: str, expected: int
    ) -> int: ...


class MembershipRepository(Protocol):
    def get_active(self, tenant_id: str, membership_id: str) -> Any | None: ...


class OtpChallengeRepository(Protocol):
    def lock(self, tenant_id: str, challenge_id: str) -> Any | None: ...


class SessionRepository(Protocol):
    def lock(self, tenant_id: str, session_id: str) -> Any | None: ...


class RefreshTokenRepository(Protocol):
    def lock_by_hash(self, tenant_id: str, token_hash: str) -> Any | None: ...


class IdempotencyRepository(Protocol):
    def lock(self, tenant_id: str, key: str) -> Any | None: ...


@runtime_checkable
class NovaIdUnitOfWork(Protocol):
    connection: Connection
    identities: IdentityRepository
    memberships: MembershipRepository
    otp_challenges: OtpChallengeRepository
    sessions: SessionRepository
    refresh_tokens: RefreshTokenRepository
    idempotency: IdempotencyRepository

    def __enter__(self) -> "NovaIdUnitOfWork": ...

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def lock_idempotency_key(self, tenant_id: str, key: str) -> None: ...
