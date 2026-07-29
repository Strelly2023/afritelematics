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

    def get_by_email(self, tenant_id: str, normalized_email: str) -> Any | None: ...


class MembershipRepository(Protocol):
    def get_active(self, tenant_id: str, membership_id: str) -> Any | None: ...


class OtpChallengeRepository(Protocol):
    def lock(self, tenant_id: str, challenge_id: str) -> Any | None: ...


class SessionRepository(Protocol):
    def lock(self, tenant_id: str, session_id: str) -> Any | None: ...

    def list_for_identity(self, tenant_id: str, identity_id: str) -> list[Any]: ...

    def get_for_identity(self, tenant_id: str, identity_id: str, session_id: str) -> Any | None: ...

    def revoke(self, tenant_id: str, identity_id: str, session_id: str, reason: str) -> int: ...

    def revoke_all_for_identity(
        self, tenant_id: str, identity_id: str, reason: str
    ) -> list[Any]: ...

    def touch(
        self, tenant_id: str, identity_id: str, session_id: str, *, now: str
    ) -> int: ...

    def require_step_up(
        self, tenant_id: str, identity_id: str, session_id: str, *, until: str
    ) -> int: ...

    def complete_step_up(self, tenant_id: str, identity_id: str, session_id: str) -> int: ...

    def lock_session(
        self,
        tenant_id: str,
        identity_id: str,
        session_id: str,
        *,
        locked_at: str,
    ) -> int: ...

    def unlock_session(self, tenant_id: str, identity_id: str, session_id: str) -> int: ...

    def expire_stale(self, tenant_id: str, *, now: str) -> int: ...

    def mark_compromised(
        self, tenant_id: str, identity_id: str, session_id: str, *, now: str
    ) -> Any | None: ...

    def get_active_strength(
        self, tenant_id: str, identity_id: str, session_id: str
    ) -> Any | None: ...


class RefreshTokenRepository(Protocol):
    def lock_by_hash(self, tenant_id: str, token_hash: str) -> Any | None: ...


class IdempotencyRepository(Protocol):
    def lock(self, tenant_id: str, key: str) -> Any | None: ...


class AuthenticationLockRepository(Protocol):
    def get(self, tenant_id: str, identifier_hash: str) -> Any | None: ...

    def upsert(
        self,
        tenant_id: str,
        identifier_hash: str,
        failure_count: int,
        window_started_at: str,
        locked_until: str | None,
        updated_at: str,
    ) -> None: ...

    def delete(self, tenant_id: str, identifier_hash: str) -> None: ...


class AuthorizationRepositoryProtocol(Protocol):
    def list_effective_permissions(
        self, *, tenant_id: str, membership_id: str, now: Any
    ) -> list[Any]: ...


@runtime_checkable
class NovaIdUnitOfWork(Protocol):
    connection: Connection
    identities: IdentityRepository
    memberships: MembershipRepository
    otp_challenges: OtpChallengeRepository
    sessions: SessionRepository
    refresh_tokens: RefreshTokenRepository
    idempotency: IdempotencyRepository
    authentication_locks: AuthenticationLockRepository
    authorization: AuthorizationRepositoryProtocol

    def __enter__(self) -> "NovaIdUnitOfWork": ...

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def lock_idempotency_key(self, tenant_id: str, key: str) -> None: ...

    def bump_identity_security_version(self, tenant_id: str, identity_id: str) -> None: ...
