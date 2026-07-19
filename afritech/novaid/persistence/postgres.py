"""Explicit psycopg persistence for security-sensitive NovaID operations."""
# ruff: noqa: E501 -- explicit tenant-bound SQL remains visible.

from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime
from decimal import Decimal
import json
from typing import Any
from uuid import UUID

from .pool import NovaIDPostgresPool
from ..domain.models import Identity

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - startup factory reports the dependency error
    psycopg = None
    dict_row = None


class PostgresRepository:
    def __init__(self, connection: Any) -> None:
        self.connection = connection


def _portable_value(value: Any) -> Any:
    if isinstance(value, (datetime, UUID)):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return value


class BufferedResult:
    def __init__(self, rows: list[Any], rowcount: int) -> None:
        self._rows, self.rowcount = rows, rowcount

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return self._rows


class PortablePostgresConnection:
    """Expose a stable DB-API-shaped connection to backend-neutral services."""

    def __init__(self, uow: "PostgresNovaIdUnitOfWork") -> None:
        self.uow = uow

    @property
    def in_transaction(self) -> bool:
        return self.uow._connection is not None

    @staticmethod
    def _statement(statement: str) -> str:
        if "INSERT OR REPLACE INTO novaid_authentication_locks" in statement:
            return (
                "INSERT INTO novaid_authentication_locks VALUES(%s,%s,%s,%s,%s,%s) "
                "ON CONFLICT(tenant_id,identifier_hash) DO UPDATE SET "
                "failure_count=EXCLUDED.failure_count,window_started_at=EXCLUDED.window_started_at,"
                "locked_until=EXCLUDED.locked_until,updated_at=EXCLUDED.updated_at"
            )
        return statement.replace("?", "%s")

    @staticmethod
    def _rows(cursor: Any) -> list[Any]:
        if cursor.description is None:
            return []
        return [
            {key: _portable_value(value) for key, value in row.items()}
            if isinstance(row, dict)
            else row
            for row in cursor.fetchall()
        ]

    def execute(self, statement: str, parameters: tuple[Any, ...] = ()):
        sql = self._statement(statement)
        if self.uow._connection is not None:
            cursor = self.uow._connection.execute(sql, parameters)
            return BufferedResult(self._rows(cursor), cursor.rowcount)
        with self.uow.pool.connection() as connection:
            cursor = connection.execute(sql, parameters)
            result = BufferedResult(self._rows(cursor), cursor.rowcount)
            connection.commit()
            return result


class PostgresTenantRepository(PostgresRepository):
    def get_active(self, tenant_id: str) -> dict[str, Any] | None:
        return self.connection.execute(
            "SELECT * FROM novaid_tenants WHERE tenant_id=%s AND status='ACTIVE'", (tenant_id,)
        ).fetchone()


class PostgresIdentityRepository(PostgresRepository):
    def get_for_tenant(self, tenant_id: str, identity_id: str, *, lock: bool = False):
        suffix = " FOR UPDATE" if lock else ""
        return self.connection.execute(
            "SELECT * FROM novaid_identities WHERE tenant_id=%s AND identity_id=%s" + suffix,
            (tenant_id, identity_id),
        ).fetchone()

    def increment_security_version(self, tenant_id: str, identity_id: str, expected: int) -> int:
        row = self.connection.execute(
            "UPDATE novaid_identities SET security_version=security_version+1,version=version+1 "
            "WHERE tenant_id=%s AND identity_id=%s AND version=%s RETURNING security_version",
            (tenant_id, identity_id, expected),
        ).fetchone()
        if not row:
            raise RuntimeError("CONCURRENCY_CONFLICT")
        return int(row["security_version"])


class PostgresMembershipRepository(PostgresRepository):
    def get_active(self, tenant_id: str, membership_id: str):
        return self.connection.execute(
            "SELECT * FROM novaid_tenant_memberships WHERE tenant_id=%s AND membership_id=%s AND status='ACTIVE'",
            (tenant_id, membership_id),
        ).fetchone()


class PostgresCredentialRepository(PostgresRepository):
    pass


class PostgresPasswordCredentialRepository(PostgresRepository):
    pass


class PostgresOtpChallengeRepository(PostgresRepository):
    def lock(self, tenant_id: str, challenge_id: str):
        return self.connection.execute(
            "SELECT * FROM novaid_otp_challenges WHERE tenant_id=%s AND challenge_id=%s FOR UPDATE",
            (tenant_id, challenge_id),
        ).fetchone()


class PostgresSessionRepository(PostgresRepository):
    def lock(self, tenant_id: str, session_id: str):
        return self.connection.execute(
            "SELECT * FROM novaid_authentication_sessions WHERE tenant_id=%s AND session_id=%s FOR UPDATE",
            (tenant_id, session_id),
        ).fetchone()


class PostgresRefreshTokenFamilyRepository(PostgresRepository):
    pass


class PostgresRefreshTokenRepository(PostgresRepository):
    def lock_by_hash(self, tenant_id: str, token_hash: str):
        return self.connection.execute(
            "SELECT * FROM novaid_refresh_tokens WHERE tenant_id=%s AND token_hash=%s FOR UPDATE",
            (tenant_id, token_hash),
        ).fetchone()


class PostgresAuthenticationAttemptRepository(PostgresRepository):
    pass


class PostgresRiskStateRepository(PostgresRepository):
    pass


class PostgresSecurityEventRepository(PostgresRepository):
    pass


class PostgresIdempotencyRepository(PostgresRepository):
    def lock(self, tenant_id: str, key: str):
        return self.connection.execute(
            "SELECT * FROM novaid_idempotency_records WHERE tenant_id=%s AND idempotency_key=%s FOR UPDATE",
            (tenant_id, key),
        ).fetchone()


class PostgresNovaIdUnitOfWork(AbstractContextManager["PostgresNovaIdUnitOfWork"]):
    def __init__(self, dsn: str | None = None, *, pool: NovaIDPostgresPool | None = None) -> None:
        if psycopg is None:
            raise RuntimeError("psycopg_required_for_postgres")
        if pool is None and not dsn:
            raise ValueError("postgres_dsn_required")
        self.pool = pool or NovaIDPostgresPool(str(dsn))
        self._connection = None
        self.connection = PortablePostgresConnection(self)
        self.identities = PostgresIdentityRepository(self.connection)
        self.memberships = PostgresMembershipRepository(self.connection)
        self.credentials = PostgresCredentialRepository(self.connection)
        self.password_credentials = PostgresPasswordCredentialRepository(self.connection)
        self.otp_challenges = PostgresOtpChallengeRepository(self.connection)
        self.sessions = PostgresSessionRepository(self.connection)
        self.refresh_families = PostgresRefreshTokenFamilyRepository(self.connection)
        self.refresh_tokens = PostgresRefreshTokenRepository(self.connection)
        self.attempts = PostgresAuthenticationAttemptRepository(self.connection)
        self.risk_states = PostgresRiskStateRepository(self.connection)
        self.security_events = PostgresSecurityEventRepository(self.connection)
        self.idempotency = PostgresIdempotencyRepository(self.connection)

    def __enter__(self) -> "PostgresNovaIdUnitOfWork":
        if self._connection is not None:
            raise RuntimeError("nested_novaid_transaction")
        self._connection = self.pool.acquire()
        self._connection.execute("BEGIN")
        return self

    def commit(self) -> None:
        if self._connection is not None:
            self._connection.commit()

    def rollback(self) -> None:
        if self._connection is not None:
            self._connection.rollback()

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        try:
            self.rollback() if exc_type else self.commit()
        finally:
            connection, self._connection = self._connection, None
            if connection is not None:
                self.pool.release(connection)
        return False

    def create_tenant(self, tenant_id: str, name: str, now: datetime) -> None:
        self.connection.execute(
            "INSERT INTO novaid_tenants(tenant_id,name,status,created_at,updated_at,version) "
            "VALUES(?,?, 'ACTIVE',?,?,1)",
            (tenant_id, name, now, now),
        )

    def add_identity(self, identity: Identity) -> None:
        self.connection.execute(
            "INSERT INTO novaid_identities(identity_id,tenant_id,normalized_email,status,created_at,"
            "updated_at,version,security_version) VALUES(?,?,?,?,?,?,?,1)",
            (
                identity.identity_id,
                identity.tenant_id,
                identity.normalized_email.lower(),
                str(identity.status),
                identity.created_at,
                identity.updated_at,
                identity.version,
            ),
        )

    def lock_idempotency_key(self, tenant_id: str, key: str) -> None:
        self.connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(?,0))",
            (f"{tenant_id}:{key}",),
        )

    def close(self) -> None:
        self.pool.close()
