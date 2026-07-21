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

    def get_by_email(self, tenant_id: str, normalized_email: str) -> Any | None:
        return self.connection.execute(
            "SELECT identity_id FROM novaid_identities "
            "WHERE tenant_id=%s AND normalized_email=%s AND status='ACTIVE'",
            (tenant_id, normalized_email.lower()),
        ).fetchone()

    def list_password_credentials(self, tenant_id: str, identity_id: str) -> list[Any]:
        rows = self.connection.execute(
            "SELECT c.credential_id,c.status,p.password_hash,c.created_at "
            "FROM novaid_credentials c JOIN novaid_password_credentials p "
            "ON p.credential_id=c.credential_id "
            "WHERE c.tenant_id=%s AND c.identity_id=%s AND c.kind='PASSWORD' "
            "ORDER BY c.created_at DESC",
            (tenant_id, identity_id),
        ).fetchall()
        return [dict(row) for row in rows]

    def supersede_active_password_credentials(self, tenant_id: str, identity_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_credentials SET status='SUPERSEDED',updated_at=%s,version=version+1 "
            "WHERE tenant_id=%s AND identity_id=%s AND kind='PASSWORD' AND status='ACTIVE'",
            (now, tenant_id, identity_id),
        )
        return row.rowcount

    def insert_password_credential(
        self,
        credential_id: str,
        tenant_id: str,
        identity_id: str,
        password_hash: str,
        algorithm_version: str,
        *,
        now: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_credentials(credential_id,tenant_id,identity_id,kind,status,created_at,"
            "updated_at,version) VALUES(%s,%s,%s,'PASSWORD','ACTIVE',%s,%s,1)",
            (credential_id, tenant_id, identity_id, now, now),
        )
        self.connection.execute(
            "INSERT INTO novaid_password_credentials(credential_id,password_hash,algorithm_version,"
            "expires_at,compromised_at) VALUES(%s,%s,%s,NULL,NULL)",
            (credential_id, password_hash, algorithm_version),
        )

    def create_otp_challenge(
        self,
        challenge_id: str,
        tenant_id: str,
        identity_id: str,
        purpose: str,
        destination_reference: str,
        secret_hash: str,
        created_at: str,
        expires_at: str,
        maximum_attempts: int,
        status: str,
        correlation_id: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_otp_challenges(challenge_id,tenant_id,identity_id,purpose,"
            "destination_reference,secret_hash,created_at,expires_at,consumed_at,attempt_count,"
            "maximum_attempts,status,correlation_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,NULL,0,%s,%s,%s)",
            (
                challenge_id,
                tenant_id,
                identity_id,
                purpose,
                destination_reference,
                secret_hash,
                created_at,
                expires_at,
                maximum_attempts,
                status,
                correlation_id,
            ),
        )

    def get_otp_challenge(self, tenant_id: str, challenge_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT * FROM novaid_otp_challenges WHERE tenant_id=%s AND challenge_id=%s",
            (tenant_id, challenge_id),
        ).fetchone()

    def increment_otp_challenge_attempt(self, challenge_id: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_otp_challenges SET attempt_count=attempt_count+1 WHERE challenge_id=%s",
            (challenge_id,),
        )
        return row.rowcount

    def consume_otp_challenge(self, challenge_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_otp_challenges SET status='CONSUMED',consumed_at=%s "
            "WHERE challenge_id=%s AND status='PENDING'",
            (now, challenge_id),
        )
        return row.rowcount


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

    def list_for_identity(self, tenant_id: str, identity_id: str) -> list[Any]:
        rows = self.connection.execute(
            "SELECT session_id,status,authentication_strength,created_at,last_seen_at,expires_at,"
            "authenticated_at,idle_expires_at,absolute_expires_at,pending_mfa_expires_at,"
            "step_up_expires_at,device_reference "
            "FROM novaid_authentication_sessions WHERE tenant_id=%s AND identity_id=%s "
            "ORDER BY created_at DESC",
            (tenant_id, identity_id),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_for_identity(self, tenant_id: str, identity_id: str, session_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT expires_at,status,authentication_strength FROM novaid_authentication_sessions "
            "WHERE tenant_id=%s AND identity_id=%s AND session_id=%s",
            (tenant_id, identity_id, session_id),
        ).fetchone()

    def get_active_strength(self, tenant_id: str, identity_id: str, session_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT authentication_strength FROM novaid_authentication_sessions "
            "WHERE tenant_id=%s AND identity_id=%s AND session_id=%s AND status='ACTIVE'",
            (tenant_id, identity_id, session_id),
        ).fetchone()

    def revoke(self, tenant_id: str, identity_id: str, session_id: str, reason: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='REVOKED',"
            "revoked_at=NOW(),revocation_reason=%s "
            "WHERE tenant_id=%s AND identity_id=%s AND session_id=%s",
            (reason, tenant_id, identity_id, session_id),
        )
        return row.rowcount

    def revoke_all_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> list[Any]:
        rows = self.connection.execute(
            "SELECT session_id,expires_at FROM novaid_authentication_sessions "
            "WHERE tenant_id=%s AND identity_id=%s AND status NOT IN ('REVOKED','EXPIRED')",
            (tenant_id, identity_id),
        ).fetchall()
        self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='REVOKED',"
            "revoked_at=NOW(),revocation_reason=%s WHERE tenant_id=%s AND identity_id=%s "
            "AND status NOT IN ('REVOKED','EXPIRED')",
            (reason, tenant_id, identity_id),
        )
        return [dict(row) for row in rows]

    def touch(self, tenant_id: str, identity_id: str, session_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET last_seen_at=%s,idle_expires_at=%s "
            "WHERE tenant_id=%s AND identity_id=%s AND session_id=%s AND status='ACTIVE'",
            (now, now, tenant_id, identity_id, session_id),
        )
        return row.rowcount

    def require_step_up(self, tenant_id: str, identity_id: str, session_id: str, *, until: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='STEP_UP_REQUIRED',"
            "step_up_expires_at=%s WHERE tenant_id=%s AND identity_id=%s AND session_id=%s "
            "AND status='ACTIVE'",
            (until, tenant_id, identity_id, session_id),
        )
        return row.rowcount

    def complete_step_up(self, tenant_id: str, identity_id: str, session_id: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='ACTIVE',step_up_expires_at=NULL,"
            "authentication_strength='PASSWORD_OTP' WHERE tenant_id=%s AND identity_id=%s "
            "AND session_id=%s AND status='STEP_UP_REQUIRED'",
            (tenant_id, identity_id, session_id),
        )
        return row.rowcount

    def lock_session(self, tenant_id: str, identity_id: str, session_id: str, *, locked_at: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='LOCKED',locked_at=%s "
            "WHERE tenant_id=%s AND identity_id=%s AND session_id=%s "
            "AND status IN ('ACTIVE','STEP_UP_REQUIRED')",
            (locked_at, tenant_id, identity_id, session_id),
        )
        return row.rowcount

    def unlock_session(self, tenant_id: str, identity_id: str, session_id: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='ACTIVE',locked_at=NULL "
            "WHERE tenant_id=%s AND identity_id=%s AND session_id=%s AND status='LOCKED'",
            (tenant_id, identity_id, session_id),
        )
        return row.rowcount

    def expire_stale(self, tenant_id: str, *, now: str) -> int:
        expired = 0
        rules = (
            ("PENDING_MFA", "pending_mfa_expires_at", "PENDING_MFA_EXPIRY"),
            ("ACTIVE", "idle_expires_at", "IDLE_EXPIRY"),
            ("STEP_UP_REQUIRED", "step_up_expires_at", "STEP_UP_EXPIRY"),
        )
        for status, column, reason in rules:
            row = self.connection.execute(
                f"UPDATE novaid_authentication_sessions SET status='EXPIRED',expired_at=%s,"
                "revoked_at=%s,revocation_reason=%s WHERE tenant_id=%s AND status=%s "
                f"AND {column} IS NOT NULL AND {column}<=%s",
                (now, now, reason, tenant_id, status, now),
            )
            expired += row.rowcount
        row = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='EXPIRED',expired_at=%s,"
            "revoked_at=%s,revocation_reason='ABSOLUTE_EXPIRY' WHERE tenant_id=%s "
            "AND status IN ('ACTIVE','PENDING_MFA','STEP_UP_REQUIRED','LOCKED') "
            "AND COALESCE(absolute_expires_at,expires_at)<=%s",
            (now, now, tenant_id, now),
        )
        expired += row.rowcount
        return expired

    def mark_compromised(
        self, tenant_id: str, identity_id: str, session_id: str, *, now: str
    ) -> Any | None:
        row = self.connection.execute(
            "SELECT expires_at FROM novaid_authentication_sessions "
            "WHERE tenant_id=%s AND identity_id=%s AND session_id=%s",
            (tenant_id, identity_id, session_id),
        ).fetchone()
        if not row:
            return None
        self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='COMPROMISED',"
            "revoked_at=%s,compromised_at=%s,revocation_reason='SECURITY_CONTAINMENT',"
            "compromise_reason='SECURITY_CONTAINMENT' WHERE tenant_id=%s AND identity_id=%s "
            "AND session_id=%s AND status NOT IN ('COMPROMISED','REVOKED','EXPIRED')",
            (now, now, tenant_id, identity_id, session_id),
        )
        self.connection.execute(
            "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=%s "
            "WHERE tenant_id=%s AND session_id=%s AND status='ACTIVE'",
            (now, tenant_id, session_id),
        )
        return row

    def revoke_refresh_families_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=NOW() "
            "WHERE tenant_id=%s AND identity_id=%s AND status='ACTIVE'",
            (tenant_id, identity_id),
        )
        return row.rowcount


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


class PostgresAuthenticationLockRepository(PostgresRepository):
    def get(self, tenant_id: str, identifier_hash: str):
        return self.connection.execute(
            "SELECT * FROM novaid_authentication_locks WHERE tenant_id=%s AND identifier_hash=%s",
            (tenant_id, identifier_hash),
        ).fetchone()

    def upsert(
        self,
        tenant_id: str,
        identifier_hash: str,
        failure_count: int,
        window_started_at: str,
        locked_until: str | None,
        updated_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_authentication_locks(tenant_id,identifier_hash,failure_count,"
            "window_started_at,locked_until,updated_at) VALUES(%s,%s,%s,%s,%s,%s) "
            "ON CONFLICT(tenant_id,identifier_hash) DO UPDATE SET failure_count=EXCLUDED.failure_count,"
            "window_started_at=EXCLUDED.window_started_at,locked_until=EXCLUDED.locked_until,"
            "updated_at=EXCLUDED.updated_at",
            (tenant_id, identifier_hash, failure_count, window_started_at, locked_until, updated_at),
        )

    def delete(self, tenant_id: str, identifier_hash: str) -> None:
        self.connection.execute(
            "DELETE FROM novaid_authentication_locks WHERE tenant_id=%s AND identifier_hash=%s",
            (tenant_id, identifier_hash),
        )


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
        self.authentication_locks = PostgresAuthenticationLockRepository(self.connection)

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

    def list_password_credentials(self, tenant_id: str, identity_id: str) -> list[Any]:
        rows = self.connection.execute(
            "SELECT c.credential_id,c.status,p.password_hash,c.created_at "
            "FROM novaid_credentials c JOIN novaid_password_credentials p "
            "ON p.credential_id=c.credential_id "
            "WHERE c.tenant_id=%s AND c.identity_id=%s AND c.kind='PASSWORD' "
            "ORDER BY c.created_at DESC",
            (tenant_id, identity_id),
        ).fetchall()
        return [dict(row) for row in rows]

    def supersede_active_password_credentials(self, tenant_id: str, identity_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_credentials SET status='SUPERSEDED',updated_at=%s,version=version+1 "
            "WHERE tenant_id=%s AND identity_id=%s AND kind='PASSWORD' AND status='ACTIVE'",
            (now, tenant_id, identity_id),
        )
        return row.rowcount

    def insert_password_credential(
        self,
        credential_id: str,
        tenant_id: str,
        identity_id: str,
        password_hash: str,
        algorithm_version: str,
        *,
        now: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_credentials(credential_id,tenant_id,identity_id,kind,status,created_at,"
            "updated_at,version) VALUES(%s,%s,%s,'PASSWORD','ACTIVE',%s,%s,1)",
            (credential_id, tenant_id, identity_id, now, now),
        )
        self.connection.execute(
            "INSERT INTO novaid_password_credentials(credential_id,password_hash,algorithm_version,"
            "expires_at,compromised_at) VALUES(%s,%s,%s,NULL,NULL)",
            (credential_id, password_hash, algorithm_version),
        )

    def create_otp_challenge(
        self,
        challenge_id: str,
        tenant_id: str,
        identity_id: str,
        purpose: str,
        destination_reference: str,
        secret_hash: str,
        created_at: str,
        expires_at: str,
        maximum_attempts: int,
        status: str,
        correlation_id: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_otp_challenges(challenge_id,tenant_id,identity_id,purpose,"
            "destination_reference,secret_hash,created_at,expires_at,consumed_at,attempt_count,"
            "maximum_attempts,status,correlation_id) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,NULL,0,%s,%s,%s)",
            (
                challenge_id,
                tenant_id,
                identity_id,
                purpose,
                destination_reference,
                secret_hash,
                created_at,
                expires_at,
                maximum_attempts,
                status,
                correlation_id,
            ),
        )

    def get_otp_challenge(self, tenant_id: str, challenge_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT * FROM novaid_otp_challenges WHERE tenant_id=%s AND challenge_id=%s",
            (tenant_id, challenge_id),
        ).fetchone()

    def increment_otp_challenge_attempt(self, challenge_id: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_otp_challenges SET attempt_count=attempt_count+1 WHERE challenge_id=%s",
            (challenge_id,),
        )
        return row.rowcount

    def consume_otp_challenge(self, challenge_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_otp_challenges SET status='CONSUMED',consumed_at=%s "
            "WHERE challenge_id=%s AND status='PENDING'",
            (now, challenge_id),
        )
        return row.rowcount

    def get_by_email(self, tenant_id: str, normalized_email: str) -> Any | None:
        return self.connection.execute(
            "SELECT identity_id FROM novaid_identities "
            "WHERE tenant_id=%s AND normalized_email=%s AND status='ACTIVE'",
            (tenant_id, normalized_email.lower()),
        ).fetchone()

    def bump_identity_security_version(self, tenant_id: str, identity_id: str) -> None:
        row = self.identities.get_for_tenant(tenant_id, identity_id)
        if row is None:
            raise LookupError("TENANT_ACCESS_DENIED")
        self.identities.increment_security_version(tenant_id, identity_id, int(row["version"]))

    def revoke_refresh_families_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> int:
        del reason
        row = self.connection.execute(
            "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=NOW() "
            "WHERE tenant_id=%s AND identity_id=%s AND status='ACTIVE'",
            (tenant_id, identity_id),
        )
        return row.rowcount

    def get_recovery_authorization_context(
        self, tenant_id: str, identity_id: str, session_id: str
    ) -> Any | None:
        return self.connection.execute(
            "SELECT s.status,s.authentication_strength,s.step_up_expires_at,m.status membership_status "
            "FROM novaid_authentication_sessions s JOIN novaid_tenant_memberships m "
            "ON m.membership_id=s.membership_id AND m.tenant_id=s.tenant_id "
            "WHERE s.tenant_id=%s AND s.identity_id=%s AND s.session_id=%s",
            (tenant_id, identity_id, session_id),
        ).fetchone()

    def get_recovery_policy(self, tenant_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT * FROM novaid_tenant_webauthn_policies WHERE tenant_id=%s",
            (tenant_id,),
        ).fetchone()

    def supersede_recovery_codes(self, tenant_id: str, identity_id: str, *, now: str) -> None:
        self.connection.execute(
            "UPDATE novaid_recovery_code_batches SET status='SUPERSEDED',revoked_at=%s,"
            "version=version+1 WHERE tenant_id=%s AND identity_id=%s AND status='ACTIVE'",
            (now, tenant_id, identity_id),
        )
        self.connection.execute(
            "UPDATE novaid_recovery_codes SET status='SUPERSEDED',revoked_at=%s,"
            "version=version+1 WHERE tenant_id=%s AND identity_id=%s AND status='ACTIVE'",
            (now, tenant_id, identity_id),
        )

    def insert_recovery_code_batch(
        self,
        batch_id: str,
        tenant_id: str,
        identity_id: str,
        *,
        created_at: str,
        expires_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_recovery_code_batches(batch_id,tenant_id,identity_id,status,"
            "created_at,expires_at,revoked_at,version) VALUES(%s,%s,%s,'ACTIVE',%s,%s,NULL,1)",
            (batch_id, tenant_id, identity_id, created_at, expires_at),
        )

    def insert_recovery_code(
        self,
        recovery_code_id: str,
        batch_id: str,
        tenant_id: str,
        identity_id: str,
        code_hash: str,
        *,
        created_at: str,
        expires_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_recovery_codes(recovery_code_id,batch_id,tenant_id,identity_id,code_hash,"
            "status,created_at,expires_at,used_at,revoked_at,attempt_count,version) "
            "VALUES(%s,%s,%s,%s,%s,'ACTIVE',%s,%s,NULL,NULL,0,1)",
            (recovery_code_id, batch_id, tenant_id, identity_id, code_hash, created_at, expires_at),
        )

    def get_recovery_code_by_hash(
        self, tenant_id: str, identity_id: str, code_hash: str
    ) -> Any | None:
        return self.connection.execute(
            "SELECT recovery_code_id,status,expires_at FROM novaid_recovery_codes "
            "WHERE tenant_id=%s AND identity_id=%s AND code_hash=%s",
            (tenant_id, identity_id, code_hash),
        ).fetchone()

    def consume_recovery_code(self, recovery_code_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_recovery_codes SET status='USED',used_at=%s,version=version+1 "
            "WHERE recovery_code_id=%s AND status='ACTIVE'",
            (now, recovery_code_id),
        )
        return row.rowcount

    def revoke_recovery_codes(self, tenant_id: str, identity_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_recovery_codes SET status='REVOKED',revoked_at=%s,version=version+1 "
            "WHERE tenant_id=%s AND identity_id=%s AND status='ACTIVE'",
            (now, tenant_id, identity_id),
        )
        return row.rowcount

    def revoke_recovery_code_batches(self, tenant_id: str, identity_id: str, *, now: str) -> None:
        self.connection.execute(
            "UPDATE novaid_recovery_code_batches SET status='REVOKED',revoked_at=%s,version=version+1 "
            "WHERE tenant_id=%s AND identity_id=%s AND status='ACTIVE'",
            (now, tenant_id, identity_id),
        )

    def count_active_recovery_codes(self, tenant_id: str, identity_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) FROM novaid_recovery_codes WHERE tenant_id=%s AND identity_id=%s "
            "AND status='ACTIVE' AND expires_at>%s",
            (tenant_id, identity_id, now),
        ).fetchone()
        return int(row[0] if row is not None else 0)

    def lock_idempotency_key(self, tenant_id: str, key: str) -> None:
        self.connection.execute(
            "SELECT pg_advisory_xact_lock(hashtextextended(?,0))",
            (f"{tenant_id}:{key}",),
        )

    def close(self) -> None:
        self.pool.close()
