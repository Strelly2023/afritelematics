"""Explicit psycopg persistence for security-sensitive NovaID operations."""
# ruff: noqa: E501 -- explicit tenant-bound SQL remains visible.

from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime, timedelta
from decimal import Decimal
import json
from typing import Any
from uuid import UUID

from .pool import NovaIDPostgresPool
from .identity_codec import (
    encode_addresses,
    encode_contact_points,
    encode_identifiers,
    encode_identity_names,
    encode_legal_name,
    encode_metadata,
    identity_from_row,
)
from ..domain.models import Identity, RequestContext

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

    def get_tenant_status(self, tenant_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT status FROM novaid_tenants WHERE tenant_id=%s",
            (tenant_id,),
        ).fetchone()

    def get_idempotency_record(self, tenant_id: str, key: str) -> Any | None:
        return self.connection.execute(
            "SELECT payload_hash,response_json FROM novaid_idempotency_records "
            "WHERE tenant_id=%s AND idempotency_key=%s",
            (tenant_id, key),
        ).fetchone()

    def insert_idempotency_record(
        self, tenant_id: str, key: str, payload_hash: str, response_json: str, *, now: str
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_idempotency_records(tenant_id,idempotency_key,payload_hash,response_json,created_at) "
            "VALUES(%s,%s,%s,%s,%s)",
            (tenant_id, key, payload_hash, response_json, now),
        )

    def create_registration_membership(
        self, membership_id: str, tenant_id: str, identity_id: str, *, now: str
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_tenant_memberships(membership_id,tenant_id,identity_id,role,status,created_at,updated_at,version) "
            "VALUES(%s,%s,%s,'MEMBER','ACTIVE',%s,%s,1)",
            (membership_id, tenant_id, identity_id, now, now),
        )

    def get_identity_for_tenant(self, tenant_id: str, identity_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT * FROM novaid_identities WHERE identity_id=%s AND tenant_id=%s",
            (identity_id, tenant_id),
        ).fetchone()

    def activate_identity(self, tenant_id: str, identity_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_identities SET status='ACTIVE',updated_at=%s,version=version+1 "
            "WHERE identity_id=%s AND tenant_id=%s",
            (now, identity_id, tenant_id),
        )
        return row.rowcount

    def create_registration_challenge(
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
        correlation_id: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_otp_challenges(challenge_id,tenant_id,identity_id,purpose,destination_reference,"
            "secret_hash,created_at,expires_at,consumed_at,attempt_count,maximum_attempts,status,correlation_id) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,NULL,0,%s,'PENDING',%s)",
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
                correlation_id,
            ),
        )

    def create_authentication_session(
        self,
        session_id: str,
        tenant_id: str,
        identity_id: str,
        authentication_time: str,
        authentication_strength: str,
        credential_id: str,
        risk_score: float,
        membership_id: str,
        *,
        created_at: str,
        expires_at: str,
        pending_mfa_expires_at: str,
        authentication_methods: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_authentication_sessions(session_id,tenant_id,identity_id,authentication_time,"
            "authentication_strength,credential_id,device_reference,client_reference,risk_score,status,created_at,"
            "last_seen_at,expires_at,revoked_at,revocation_reason,version,membership_id,authenticated_at,"
            "idle_expires_at,absolute_expires_at,pending_mfa_expires_at,step_up_expires_at,locked_at,expired_at,"
            "compromised_at,network_reference,authentication_methods,security_version,revoked_by,compromise_reason) "
            "VALUES(%s,%s,%s,%s,%s,%s,NULL,NULL,%s,'PENDING_MFA',%s,%s,%s,NULL,NULL,1,%s,NULL,%s,%s,%s,NULL,NULL,NULL,NULL,NULL,%s,1,NULL,NULL)",
            (
                session_id,
                tenant_id,
                identity_id,
                authentication_time,
                authentication_strength,
                credential_id,
                risk_score,
                created_at,
                created_at,
                expires_at,
                membership_id,
                created_at,
                expires_at,
                pending_mfa_expires_at,
                authentication_methods,
            ),
        )

    def create_login_challenge(
        self,
        challenge_id: str,
        tenant_id: str,
        identity_id: str,
        session_id: str,
        secret_hash: str,
        created_at: str,
        expires_at: str,
        correlation_id: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_otp_challenges(challenge_id,tenant_id,identity_id,purpose,destination_reference,"
            "secret_hash,created_at,expires_at,consumed_at,attempt_count,maximum_attempts,status,correlation_id) "
            "VALUES(%s,%s,%s,'LOGIN',%s,%s,%s,%s,NULL,0,5,'PENDING',%s)",
            (challenge_id, tenant_id, identity_id, session_id, secret_hash, created_at, expires_at, correlation_id),
        )

    def get_pending_session(self, tenant_id: str, session_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT identity_id,status,expires_at FROM novaid_authentication_sessions "
            "WHERE tenant_id=%s AND session_id=%s",
            (tenant_id, session_id),
        ).fetchone()

    def get_recent_login_challenge(
        self, tenant_id: str, identity_id: str, session_id: str
    ) -> Any | None:
        return self.connection.execute(
            "SELECT challenge_id,created_at FROM novaid_otp_challenges "
            "WHERE tenant_id=%s AND identity_id=%s AND purpose='LOGIN' "
            "AND destination_reference=%s AND status='PENDING' ORDER BY created_at DESC LIMIT 1",
            (tenant_id, identity_id, session_id),
        ).fetchone()

    def get_login_identity(self, tenant_id: str, normalized_email: str) -> Any | None:
        return self.connection.execute(
            "SELECT i.identity_id,i.status,m.membership_id,c.credential_id,p.password_hash "
            "FROM novaid_identities i JOIN novaid_tenant_memberships m ON m.identity_id=i.identity_id AND m.tenant_id=i.tenant_id "
            "JOIN novaid_credentials c ON c.identity_id=i.identity_id AND c.tenant_id=i.tenant_id "
            "JOIN novaid_password_credentials p ON p.credential_id=c.credential_id "
            "WHERE i.tenant_id=%s AND i.normalized_email=%s AND m.status='ACTIVE' AND c.status='ACTIVE'",
            (tenant_id, normalized_email.lower()),
        ).fetchone()

    def update_otp_status(self, challenge_id: str, status: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_otp_challenges SET status=%s WHERE challenge_id=%s",
            (status, challenge_id),
        )
        return row.rowcount

    def supersede_challenge(self, challenge_id: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_otp_challenges SET status='SUPERSEDED' WHERE challenge_id=%s",
            (challenge_id,),
        )
        return row.rowcount

    def get_mfa_challenge_session(self, tenant_id: str, challenge_id: str, session_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT c.*,s.identity_id,s.status session_status FROM novaid_otp_challenges c "
            "JOIN novaid_authentication_sessions s ON CAST(s.session_id AS TEXT)=c.destination_reference "
            "WHERE c.challenge_id=%s AND c.tenant_id=%s AND s.session_id=%s",
            (challenge_id, tenant_id, session_id),
        ).fetchone()

    def activate_session_and_refresh(
        self,
        session_id: str,
        *,
        now: str,
        authentication_methods: str,
    ) -> int:
        idle_expires_at = (
            datetime.fromisoformat(now) + timedelta(minutes=30)
        ).isoformat()

        row = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='ACTIVE',"
            "authentication_strength='PASSWORD_OTP',authenticated_at=%s,"
            "last_seen_at=%s,idle_expires_at=%s,authentication_methods=%s,"
            "pending_mfa_expires_at=NULL WHERE session_id=%s "
            "AND status='PENDING_MFA'",
            (
                now,
                now,
                idle_expires_at,
                authentication_methods,
                session_id,
            ),
        )
        return row.rowcount

    def create_refresh_family(
        self,
        family_id: str,
        session_id: str,
        identity_id: str,
        tenant_id: str,
        *,
        created_at: str,
        expires_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_refresh_token_families(family_id,session_id,identity_id,tenant_id,status,created_at,expires_at,revoked_at,version) "
            "VALUES(%s,%s,%s,%s,'ACTIVE',%s,%s,NULL,1)",
            (family_id, session_id, identity_id, tenant_id, created_at, expires_at),
        )

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
        self.connection.execute(
            "INSERT INTO novaid_refresh_tokens(token_id,family_id,session_id,identity_id,tenant_id,token_hash,parent_token_id,issued_at,expires_at,used_at,revoked_at,replacement_token_id,status) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,NULL,NULL,NULL,'ACTIVE')",
            (token_id, family_id, session_id, identity_id, tenant_id, token_hash, parent_token_id, issued_at, expires_at),
        )

    def get_refresh_context(self, tenant_id: str, token_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT t.*,f.status family_status,s.status session_status,"
            "s.idle_expires_at,s.absolute_expires_at,s.expires_at session_expires_at "
            "FROM novaid_refresh_tokens t "
            "JOIN novaid_refresh_token_families f ON f.family_id=t.family_id "
            "JOIN novaid_authentication_sessions s ON s.session_id=t.session_id "
            "WHERE t.token_id=%s AND t.tenant_id=%s",
            (token_id, tenant_id),
        ).fetchone()

    def mark_refresh_replayed(self, token_id: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_refresh_tokens SET status='REPLAYED' WHERE token_id=%s",
            (token_id,),
        )
        return row.rowcount

    def revoke_refresh_family(self, family_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=%s WHERE family_id=%s",
            (now, family_id),
        )
        return row.rowcount

    def revoke_refresh_session(self, session_id: str, *, now: str, reason: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='REVOKED',revoked_at=%s,revocation_reason=%s "
            "WHERE session_id=%s",
            (now, reason, session_id),
        )
        return row.rowcount

    def expire_refresh_session(self, tenant_id: str, session_id: str, *, now: str, reason: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='EXPIRED',expired_at=%s,revoked_at=%s,revocation_reason=%s "
            "WHERE tenant_id=%s AND session_id=%s AND status='ACTIVE'",
            (now, now, reason, tenant_id, session_id),
        )
        return row.rowcount

    def mark_refresh_used(self, token_id: str, successor_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_refresh_tokens SET status='USED',used_at=%s,replacement_token_id=%s "
            "WHERE token_id=%s AND status='ACTIVE'",
            (now, successor_id, token_id),
        )
        return row.rowcount

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
    def add(self, event: Any) -> None:
        self.connection.execute(
            "INSERT INTO novaid_security_events(event_id,event_type,severity,tenant_id,actor_identity_id,"
            "subject_identity_id,correlation_id,request_id,occurred_at,recorded_at,outcome,reason_codes,metadata,schema_version) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                event.event_id,
                event.event_type,
                event.severity,
                event.tenant_id,
                event.actor_identity_id,
                event.subject_identity_id,
                event.correlation_id,
                event.request_id,
                event.occurred_at,
                event.recorded_at,
                event.outcome,
                json.dumps(event.reason_codes),
                json.dumps(event.metadata),
                event.schema_version,
            ),
        )


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

    @property
    def in_transaction(self) -> bool:
        return bool(self._connection and self._connection.in_transaction)

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

    def get_identity(
        self,
        context: RequestContext,
        identity_id: str,
    ) -> Identity:
        row = self.connection.execute(
            "SELECT * FROM novaid_identities "
            "WHERE identity_id=? AND tenant_id=?",
            (identity_id, context.tenant_id),
        ).fetchone()

        if row is None:
            raise LookupError("TENANT_ACCESS_DENIED")

        return identity_from_row(row)

    def add_identity(self, identity: Identity) -> None:
        self.connection.execute(
            "INSERT INTO novaid_identities("
            "identity_id,tenant_id,normalized_email,status,created_at,"
            "updated_at,version,security_version,identity_type,legal_name,"
            "preferred_name,alternative_names,contact_points,addresses,"
            "identifiers,verification_status,assurance_level,metadata"
            ") VALUES("
            "?,?,?,?,?,?,?,1,?,?::jsonb,?,?::jsonb,?::jsonb,"
            "?::jsonb,?::jsonb,?,?,?::jsonb"
            ")",
            (
                identity.identity_id,
                identity.tenant_id,
                identity.normalized_email.lower(),
                identity.status.value,
                identity.created_at,
                identity.updated_at,
                identity.version,
                identity.identity_type.value,
                encode_legal_name(identity.legal_name),
                identity.preferred_name,
                encode_identity_names(identity.alternative_names),
                encode_contact_points(identity.contact_points),
                encode_addresses(identity.addresses),
                encode_identifiers(identity.identifiers),
                identity.verification_status.value,
                identity.assurance_level.value,
                encode_metadata(identity.metadata),
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

    def record_security_event(self, event: Any) -> None:
        self.security_events.add(event)

    def revoke_refresh_families_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> int:
        del reason
        row = self.connection.execute(
            "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=NOW() "
            "WHERE tenant_id=%s AND identity_id=%s AND status='ACTIVE'",
            (tenant_id, identity_id),
        )
        return row.rowcount

    def revoke_webauthn_credentials_for_identity(self, tenant_id: str, identity_id: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_webauthn_credentials SET status='SUSPENDED',version=version+1 "
            "WHERE tenant_id=%s AND identity_id=%s AND status='ACTIVE'",
            (tenant_id, identity_id),
        )
        return row.rowcount

    def list_active_webauthn_credentials(self, tenant_id: str, identity_id: str) -> list[Any]:
        return self.connection.execute(
            "SELECT credential_id,transports FROM novaid_webauthn_credentials "
            "WHERE tenant_id=%s AND identity_id=%s AND status IN ('ACTIVE','SUSPENDED')",
            (tenant_id, identity_id),
        ).fetchall()

    def get_webauthn_credential(self, tenant_id: str, credential_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT * FROM novaid_webauthn_credentials WHERE tenant_id=%s AND credential_id=%s",
            (tenant_id, credential_id),
        ).fetchone()

    def get_passwordless_session_context(self, tenant_id: str, identity_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT m.membership_id,i.status,i.security_version FROM novaid_tenant_memberships m "
            "JOIN novaid_identities i ON i.identity_id=m.identity_id AND i.tenant_id=m.tenant_id "
            "WHERE m.tenant_id=%s AND m.identity_id=%s AND m.status='ACTIVE' AND i.status='ACTIVE'",
            (tenant_id, identity_id),
        ).fetchone()

    def get_webauthn_session(self, tenant_id: str, session_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT identity_id,status FROM novaid_authentication_sessions "
            "WHERE tenant_id=%s AND session_id=%s",
            (tenant_id, session_id),
        ).fetchone()

    def insert_webauthn_challenge(
        self,
        table: str,
        *,
        challenge_id: str,
        tenant_id: str,
        identity_id: str | None,
        session_id: str | None,
        purpose: str,
        challenge_hash: str,
        rp_id: str,
        origin: str,
        created_at: str,
        expires_at: str,
        correlation_id: str,
        request_id: str,
        maximum_attempts: int,
    ) -> None:
        columns = "challenge_id,tenant_id,identity_id,"
        values: tuple[object, ...]
        if table == "novaid_webauthn_authentication_challenges":
            columns += "session_id,"
            values = (challenge_id, tenant_id, identity_id, session_id)
            placeholders = "%s,%s,%s,%s"
        else:
            values = (challenge_id, tenant_id, identity_id)
            placeholders = "%s,%s,%s"
        columns += (
            "purpose,challenge_hash,rp_id,origin,created_at,expires_at,consumed_at,status,"
            "attempt_count,maximum_attempts,correlation_id,request_id"
        )
        values += (
            purpose,
            challenge_hash,
            rp_id,
            origin,
            created_at,
            expires_at,
            None,
            "PENDING",
            0,
            maximum_attempts,
            correlation_id,
            request_id,
        )
        self.connection.execute(
            f"INSERT INTO {table}({columns}) VALUES({placeholders},%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            values,
        )

    def get_webauthn_challenge(
        self, table: str, challenge_id: str, tenant_id: str
    ) -> Any | None:
        return self.connection.execute(
            f"SELECT * FROM {table} WHERE challenge_id=%s AND tenant_id=%s",
            (challenge_id, tenant_id),
        ).fetchone()

    def consume_webauthn_challenge(
        self, table: str, challenge_id: str, tenant_id: str, *, now: str
    ) -> int:
        row = self.connection.execute(
            f"UPDATE {table} SET status='CONSUMED',consumed_at=%s "
            "WHERE challenge_id=%s AND tenant_id=%s AND status='PENDING'",
            (now, challenge_id, tenant_id),
        )
        return row.rowcount

    def insert_webauthn_authenticator(
        self,
        authenticator_id: str,
        tenant_id: str,
        aaguid: str,
        friendly_name: str | None,
        *,
        status: str,
        created_at: str,
        updated_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_authenticators VALUES(%s,%s,%s,%s,%s,%s,%s,1)",
            (
                authenticator_id,
                tenant_id,
                aaguid,
                friendly_name,
                status,
                created_at,
                updated_at,
            ),
        )

    def insert_webauthn_credential(
        self,
        *,
        credential_id: str,
        tenant_id: str,
        identity_id: str,
        membership_id: str,
        authenticator_id: str,
        user_handle: bytes,
        public_key_cose: bytes,
        public_key_algorithm: int,
        sign_count: int,
        aaguid: str,
        attestation_format: str,
        attestation_type: str,
        transports: str,
        backup_eligible: bool,
        backup_state: bool,
        discoverable: bool,
        resident_key: bool,
        user_verification: bool,
        created_at: str,
        status: str,
        version: int,
        friendly_name: str | None,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_webauthn_credentials(credential_id,tenant_id,identity_id,"
            "membership_id,authenticator_id,user_handle,public_key_cose,public_key_algorithm,"
            "sign_count,aaguid,attestation_format,attestation_type,transports,backup_eligible,"
            "backup_state,discoverable,resident_key,user_verification,created_at,status,version,"
            "friendly_name) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                credential_id,
                tenant_id,
                identity_id,
                membership_id,
                authenticator_id,
                user_handle,
                public_key_cose,
                public_key_algorithm,
                sign_count,
                aaguid,
                attestation_format,
                attestation_type,
                transports,
                backup_eligible,
                backup_state,
                discoverable,
                resident_key,
                user_verification,
                created_at,
                status,
                version,
                friendly_name,
            ),
        )

    def mark_webauthn_credential_compromised(self, tenant_id: str, credential_id: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_webauthn_credentials SET status='COMPROMISED',version=version+1 "
            "WHERE tenant_id=%s AND credential_id=%s AND status='ACTIVE'",
            (tenant_id, credential_id),
        )
        return row.rowcount

    def update_webauthn_credential_sign_count(
        self,
        tenant_id: str,
        credential_id: str,
        *,
        new_sign_count: int,
        last_used_at: str,
        last_verified_at: str,
        backup_state: bool,
        expected_sign_count: int,
    ) -> int:
        row = self.connection.execute(
            "UPDATE novaid_webauthn_credentials SET sign_count=%s,last_used_at=%s,"
            "last_verified_at=%s,backup_state=%s,version=version+1 WHERE tenant_id=%s "
            "AND credential_id=%s AND status='ACTIVE' AND sign_count=%s",
            (
                new_sign_count,
                last_used_at,
                last_verified_at,
                backup_state,
                tenant_id,
                credential_id,
                expected_sign_count,
            ),
        )
        return row.rowcount

    def update_webauthn_credential_status(
        self,
        tenant_id: str,
        identity_id: str,
        credential_id: str,
        *,
        target: str,
    ) -> int:
        row = self.connection.execute(
            "UPDATE novaid_webauthn_credentials SET status=%s,version=version+1 "
            "WHERE tenant_id=%s AND identity_id=%s AND credential_id=%s",
            (target, tenant_id, identity_id, credential_id),
        )
        return row.rowcount

    def complete_webauthn_step_up(self, tenant_id: str, session_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='ACTIVE',"
            "authentication_strength='PHISHING_RESISTANT',authenticated_at=%s,"
            "step_up_expires_at=%s,authentication_methods='[\"WEBAUTHN\"]' "
            "WHERE tenant_id=%s AND session_id=%s AND status='STEP_UP_REQUIRED'",
            (now, (datetime.fromisoformat(now) + timedelta(minutes=5)).isoformat(), tenant_id, session_id),
        )
        return row.rowcount

    def insert_webauthn_status_history(
        self,
        history_id: str,
        tenant_id: str,
        credential_id: str,
        previous_status: str,
        target_status: str,
        reason: str,
        created_at: str,
        actor_identity_id: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_authenticator_status_history VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                history_id,
                tenant_id,
                credential_id,
                previous_status,
                target_status,
                reason,
                created_at,
                actor_identity_id,
            ),
        )

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

    def replace_tenant_webauthn_policy(
        self,
        tenant_id: str,
        policy: dict[str, object],
        *,
        updated_by: str,
        reason: str,
        version: int,
        updated_at: str,
    ) -> None:
        del reason
        self.connection.execute(
            "DELETE FROM novaid_tenant_webauthn_policies WHERE tenant_id=%s",
            (tenant_id,),
        )
        self.connection.execute(
            "INSERT INTO novaid_tenant_webauthn_policies(tenant_id,require_webauthn,"
            "passkeys_enabled,passwordless_enabled,require_phishing_resistant_step_up,"
            "user_verification,attestation,maximum_credentials,recovery_codes_enabled,"
            "recovery_code_count,recovery_code_expiry_days,recovery_approval_count,"
            "recovery_requires_new_authenticator,step_up_seconds,updated_at,updated_by,version) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                tenant_id,
                bool(policy["enabled"]),
                bool(policy["passkeys_enabled"]),
                bool(policy["passwordless_enabled"]),
                bool(policy["phishing_resistant_step_up_required"]),
                policy["user_verification"],
                policy["attestation"],
                int(policy["maximum_credentials"]),
                bool(policy["recovery_codes_enabled"]),
                int(policy["recovery_code_count"]),
                int(policy["recovery_code_expiry_days"]),
                int(policy["recovery_approval_count"]),
                bool(policy["recovery_requires_new_authenticator"]),
                int(policy["step_up_seconds"]),
                updated_at,
                updated_by,
                version,
            ),
        )
        self.connection.execute(
            "UPDATE novaid_tenant_webauthn_policy_history SET status='SUPERSEDED' "
            "WHERE tenant_id=%s AND status='ACTIVE'",
            (tenant_id,),
        )
        self.connection.execute(
            "INSERT INTO novaid_tenant_webauthn_policy_history(policy_history_id,tenant_id,"
            "policy_version,status,policy,reason,created_at,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
            (
                _id(),
                tenant_id,
                version,
                "ACTIVE",
                json.dumps(policy, sort_keys=True, separators=(",", ":")),
                reason,
                updated_at,
                updated_by,
            ),
        )

    def get_actor_recovery_context(
        self, tenant_id: str, actor_identity_id: str, session_id: str
    ) -> Any | None:
        return self.connection.execute(
            "SELECT m.role,s.authentication_strength,s.step_up_expires_at FROM novaid_tenant_memberships m "
            "JOIN novaid_authentication_sessions s ON s.membership_id=m.membership_id "
            "WHERE m.tenant_id=%s AND m.identity_id=%s AND m.status='ACTIVE' AND s.session_id=%s AND s.status='ACTIVE'",
            (tenant_id, actor_identity_id, session_id),
        ).fetchone()

    def get_active_identity_by_email(self, tenant_id: str, normalized_email: str) -> Any | None:
        return self.connection.execute(
            "SELECT identity_id FROM novaid_identities WHERE tenant_id=%s AND normalized_email=%s AND status='ACTIVE'",
            (tenant_id, normalized_email),
        ).fetchone()

    def get_recent_recovery_request(self, tenant_id: str, identity_id: str, *, since: str) -> Any | None:
        return self.connection.execute(
            "SELECT recovery_request_id FROM novaid_account_recovery_requests WHERE tenant_id=%s "
            "AND identity_id=%s AND requested_at>%s AND status NOT IN "
            "('REJECTED','COMPLETED','CANCELLED','EXPIRED')",
            (tenant_id, identity_id, since),
        ).fetchone()

    def insert_recovery_request(
        self,
        recovery_request_id: str,
        tenant_id: str,
        identity_id: str,
        *,
        status: str,
        recovery_method: str,
        requested_at: str,
        expires_at: str,
        reason: str,
        correlation_id: str,
        request_id: str,
        device_reference: str | None,
        network_reference: str | None,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_account_recovery_requests(recovery_request_id,tenant_id,identity_id,"
            "status,recovery_method,requested_at,expires_at,approved_at,approved_by,completed_at,"
            "rejected_at,cancelled_at,reason,correlation_id,request_id,device_reference,"
            "network_reference,version) VALUES(%s,%s,%s,%s,%s,%s,%s,NULL,NULL,NULL,NULL,NULL,%s,%s,%s,%s,%s,1)",
            (
                recovery_request_id,
                tenant_id,
                identity_id,
                status,
                recovery_method,
                requested_at,
                expires_at,
                reason,
                correlation_id,
                request_id,
                device_reference,
                network_reference,
            ),
        )

    def get_recovery_request(self, tenant_id: str, recovery_request_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT * FROM novaid_account_recovery_requests WHERE tenant_id=%s AND recovery_request_id=%s",
            (tenant_id, recovery_request_id),
        ).fetchone()

    def mark_recovery_verified(self, recovery_request_id: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET status='VERIFIED',version=version+1 "
            "WHERE recovery_request_id=%s AND status='REQUESTED'",
            (recovery_request_id,),
        )
        return row.rowcount

    def insert_recovery_evidence(
        self,
        evidence_id: str,
        recovery_request_id: str,
        tenant_id: str,
        identity_id: str,
        *,
        method: str,
        correlation_id: str,
        request_id: str,
        created_at: str,
    ) -> None:
        self.connection.execute(
            "INSERT INTO novaid_account_recovery_evidence(evidence_id,recovery_request_id,"
            "tenant_id,identity_id,method,result,risk_indicators,actor_identity_id,"
            "correlation_id,request_id,created_at) VALUES(%s,%s,%s,%s,%s,'VERIFIED','[]',NULL,%s,%s,%s)",
            (evidence_id, recovery_request_id, tenant_id, identity_id, method, correlation_id, request_id, created_at),
        )

    def get_membership_role_status(self, tenant_id: str, identity_id: str) -> Any | None:
        return self.connection.execute(
            "SELECT role,status FROM novaid_tenant_memberships WHERE tenant_id=%s AND identity_id=%s",
            (tenant_id, identity_id),
        ).fetchone()

    def insert_recovery_approval(
        self,
        approval_id: str,
        recovery_request_id: str,
        tenant_id: str,
        approver_identity_id: str,
        *,
        decision: str,
        reason: str,
        created_at: str,
        expires_at: str,
    ) -> None:
        del decision
        self.connection.execute(
            "INSERT INTO novaid_account_recovery_approvals(approval_id,recovery_request_id,"
            "tenant_id,approver_identity_id,decision,reason,created_at,expires_at) "
            "VALUES(%s,%s,%s,%s,'APPROVED',%s,%s,%s)",
            (approval_id, recovery_request_id, tenant_id, approver_identity_id, reason, created_at, expires_at),
        )

    def bump_recovery_request_version(self, recovery_request_id: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET version=version+1 WHERE recovery_request_id=%s",
            (recovery_request_id,),
        )
        return row.rowcount

    def count_active_recovery_approvals(
        self, tenant_id: str, recovery_request_id: str, *, now: str
    ) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) FROM novaid_account_recovery_approvals WHERE tenant_id=%s "
            "AND recovery_request_id=%s AND decision='APPROVED' AND expires_at>%s",
            (tenant_id, recovery_request_id, now),
        ).fetchone()
        return int(row[0] if row else 0)

    def mark_recovery_approved(
        self, recovery_request_id: str, *, approved_at: str, approved_by: str
    ) -> int:
        row = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET status='APPROVED',approved_at=%s,"
            "approved_by=%s,version=version+1 WHERE recovery_request_id=%s AND status='VERIFIED'",
            (approved_at, approved_by, recovery_request_id),
        )
        return row.rowcount

    def mark_recovery_rejected(
        self, tenant_id: str, recovery_request_id: str, *, rejected_at: str, reason: str
    ) -> int:
        row = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET status='REJECTED',rejected_at=%s,"
            "reason=%s,version=version+1 WHERE tenant_id=%s AND recovery_request_id=%s "
            "AND status IN ('REQUESTED','VERIFIED')",
            (rejected_at, reason, tenant_id, recovery_request_id),
        )
        return row.rowcount

    def mark_recovery_cancelled(
        self, tenant_id: str, identity_id: str, recovery_request_id: str, *, cancelled_at: str
    ) -> int:
        row = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET status='CANCELLED',cancelled_at=%s,"
            "version=version+1 WHERE tenant_id=%s AND identity_id=%s AND recovery_request_id=%s "
            "AND status IN ('REQUESTED','VERIFIED')",
            (cancelled_at, tenant_id, identity_id, recovery_request_id),
        )
        return row.rowcount

    def expire_recovery_requests(self, tenant_id: str, *, now: str) -> int:
        row = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET status='EXPIRED',version=version+1 "
            "WHERE tenant_id=%s AND expires_at<=%s AND status IN ('REQUESTED','VERIFIED','APPROVED')",
            (tenant_id, now),
        )
        return row.rowcount

    def mark_recovery_completed(
        self, tenant_id: str, recovery_request_id: str, *, completed_at: str
    ) -> Any | None:
        row = self.connection.execute(
            "SELECT identity_id,status,expires_at FROM novaid_account_recovery_requests "
            "WHERE tenant_id=%s AND recovery_request_id=%s",
            (tenant_id, recovery_request_id),
        ).fetchone()
        if not row:
            return None
        changed = self.connection.execute(
            "UPDATE novaid_account_recovery_requests SET status='COMPLETED',completed_at=%s,version=version+1 "
            "WHERE recovery_request_id=%s AND status='APPROVED'",
            (completed_at, recovery_request_id),
        )
        if changed.rowcount != 1:
            return None
        return row

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
