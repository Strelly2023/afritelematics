"""Normalized transactional adapter used for local verification.

The SQL schema mirrors the PostgreSQL migration. SQLite is intentionally only a
local test adapter and is not presented as PostgreSQL operational evidence.
"""
# ruff: noqa: E501 -- normalized DDL is kept legible and grep-friendly.

from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime, timedelta
import json
import sqlite3
from pathlib import Path
from typing import Any

from ..domain.models import Identity, IdentityStatus, RequestContext, SecurityEvent


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS novaid_tenants(
 tenant_id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('ACTIVE','SUSPENDED','DISABLED')),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_identities(
 identity_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES novaid_tenants(tenant_id), normalized_email TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('PENDING_VERIFICATION','ACTIVE','LOCKED','SUSPENDED','DISABLED','DELETED')),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
 security_version INTEGER NOT NULL DEFAULT 1,
 UNIQUE(tenant_id, normalized_email));
CREATE INDEX IF NOT EXISTS ix_novaid_identity_tenant ON novaid_identities(tenant_id);
CREATE TABLE IF NOT EXISTS novaid_tenant_memberships(
 membership_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES novaid_tenants(tenant_id),
 identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id), role TEXT NOT NULL, status TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1,
 UNIQUE(tenant_id, identity_id));
CREATE TABLE IF NOT EXISTS novaid_credentials(
 credential_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id),
 kind TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_password_credentials(
 credential_id TEXT PRIMARY KEY REFERENCES novaid_credentials(credential_id), password_hash TEXT NOT NULL,
 algorithm_version TEXT NOT NULL, expires_at TEXT, compromised_at TEXT);
CREATE TABLE IF NOT EXISTS novaid_otp_challenges(
 challenge_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id),
 purpose TEXT NOT NULL, destination_reference TEXT NOT NULL, secret_hash TEXT NOT NULL UNIQUE,
 created_at TEXT NOT NULL, expires_at TEXT NOT NULL, consumed_at TEXT, attempt_count INTEGER NOT NULL DEFAULT 0,
 maximum_attempts INTEGER NOT NULL, status TEXT NOT NULL, correlation_id TEXT NOT NULL,
 CHECK(expires_at > created_at));
CREATE TABLE IF NOT EXISTS novaid_authentication_sessions(
 session_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT NOT NULL REFERENCES novaid_identities(identity_id),
 authentication_time TEXT NOT NULL, authentication_strength TEXT NOT NULL, credential_id TEXT,
 device_reference TEXT, client_reference TEXT, risk_score REAL NOT NULL, status TEXT NOT NULL,
 created_at TEXT NOT NULL, last_seen_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT, revocation_reason TEXT,
 version INTEGER NOT NULL DEFAULT 1, membership_id TEXT, authenticated_at TEXT, idle_expires_at TEXT,
 absolute_expires_at TEXT, pending_mfa_expires_at TEXT, step_up_expires_at TEXT, locked_at TEXT,
 expired_at TEXT, compromised_at TEXT, network_reference TEXT, authentication_methods TEXT NOT NULL DEFAULT '[]',
 security_version INTEGER NOT NULL DEFAULT 1, revoked_by TEXT, compromise_reason TEXT,
 CHECK(expires_at > created_at));
CREATE INDEX IF NOT EXISTS ix_novaid_session_tenant_identity ON novaid_authentication_sessions(tenant_id,identity_id,status);
CREATE TABLE IF NOT EXISTS novaid_refresh_token_families(
 family_id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES novaid_authentication_sessions(session_id),
 identity_id TEXT NOT NULL, tenant_id TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
 expires_at TEXT NOT NULL, revoked_at TEXT, version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_refresh_tokens(
 token_id TEXT PRIMARY KEY, family_id TEXT NOT NULL REFERENCES novaid_refresh_token_families(family_id),
 session_id TEXT NOT NULL, identity_id TEXT NOT NULL, tenant_id TEXT NOT NULL, token_hash TEXT NOT NULL UNIQUE,
 parent_token_id TEXT, issued_at TEXT NOT NULL, expires_at TEXT NOT NULL, used_at TEXT, revoked_at TEXT,
 replacement_token_id TEXT, status TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS ix_novaid_refresh_family ON novaid_refresh_tokens(family_id,status);
CREATE TABLE IF NOT EXISTS novaid_authentication_attempts(
 attempt_id TEXT PRIMARY KEY, identity_id TEXT, tenant_id TEXT NOT NULL, credential_type TEXT NOT NULL,
 result TEXT NOT NULL, reason_code TEXT NOT NULL, occurred_at TEXT NOT NULL, correlation_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_identity_risk_states(
 identity_id TEXT NOT NULL, tenant_id TEXT NOT NULL, risk_score REAL NOT NULL, status TEXT NOT NULL,
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1, PRIMARY KEY(identity_id,tenant_id));
CREATE TABLE IF NOT EXISTS novaid_identity_status_history(
 transition_id TEXT PRIMARY KEY, identity_id TEXT NOT NULL, tenant_id TEXT NOT NULL, previous_status TEXT NOT NULL,
 new_status TEXT NOT NULL, reason_code TEXT NOT NULL, actor_identity_id TEXT NOT NULL, correlation_id TEXT NOT NULL,
 occurred_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_security_events(
 event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, severity TEXT NOT NULL, tenant_id TEXT NOT NULL,
 actor_identity_id TEXT NOT NULL, subject_identity_id TEXT NOT NULL, correlation_id TEXT NOT NULL,
 request_id TEXT NOT NULL, occurred_at TEXT NOT NULL, recorded_at TEXT NOT NULL, outcome TEXT NOT NULL,
 reason_codes TEXT NOT NULL, metadata TEXT NOT NULL, schema_version INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS ix_novaid_event_correlation ON novaid_security_events(correlation_id,event_type,occurred_at);
CREATE TABLE IF NOT EXISTS novaid_idempotency_records(
 tenant_id TEXT NOT NULL, idempotency_key TEXT NOT NULL, payload_hash TEXT NOT NULL,
 response_json TEXT NOT NULL, created_at TEXT NOT NULL, PRIMARY KEY(tenant_id,idempotency_key));
CREATE TABLE IF NOT EXISTS novaid_authentication_locks(
 tenant_id TEXT NOT NULL, identifier_hash TEXT NOT NULL, failure_count INTEGER NOT NULL,
 window_started_at TEXT NOT NULL, locked_until TEXT, updated_at TEXT NOT NULL,
 PRIMARY KEY(tenant_id,identifier_hash));
CREATE TABLE IF NOT EXISTS novaid_security_outbox(
 outbox_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, event_type TEXT NOT NULL,
 resource_type TEXT NOT NULL, resource_id TEXT NOT NULL, event_version INTEGER NOT NULL,
 payload TEXT NOT NULL, created_at TEXT NOT NULL, published_at TEXT,
 attempt_count INTEGER NOT NULL DEFAULT 0, last_error TEXT, next_attempt_at TEXT,
 status TEXT NOT NULL, available_at TEXT, last_attempt_at TEXT, lease_owner TEXT,
 lease_expires_at TEXT);
CREATE TABLE IF NOT EXISTS novaid_webauthn_registration_challenges(
 challenge_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT NOT NULL,
 purpose TEXT NOT NULL, challenge_hash TEXT NOT NULL, rp_id TEXT NOT NULL, origin TEXT NOT NULL,
 created_at TEXT NOT NULL, expires_at TEXT NOT NULL, consumed_at TEXT, status TEXT NOT NULL,
 attempt_count INTEGER NOT NULL, maximum_attempts INTEGER NOT NULL, correlation_id TEXT NOT NULL,
 request_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_webauthn_authentication_challenges(
 challenge_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT, session_id TEXT,
 purpose TEXT NOT NULL, challenge_hash TEXT NOT NULL, rp_id TEXT NOT NULL, origin TEXT NOT NULL,
 created_at TEXT NOT NULL, expires_at TEXT NOT NULL, consumed_at TEXT, status TEXT NOT NULL,
 attempt_count INTEGER NOT NULL, maximum_attempts INTEGER NOT NULL, correlation_id TEXT NOT NULL,
 request_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_authenticators(
 authenticator_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, aaguid TEXT NOT NULL,
 friendly_name TEXT, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_webauthn_credentials(
 credential_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT NOT NULL,
 membership_id TEXT, authenticator_id TEXT, user_handle BLOB NOT NULL, public_key_cose BLOB NOT NULL,
 public_key_algorithm INTEGER NOT NULL, sign_count INTEGER NOT NULL, aaguid TEXT NOT NULL,
 attestation_format TEXT NOT NULL, attestation_type TEXT NOT NULL, transports TEXT NOT NULL,
 backup_eligible INTEGER NOT NULL, backup_state INTEGER NOT NULL, discoverable INTEGER NOT NULL,
 resident_key INTEGER NOT NULL, user_verification INTEGER NOT NULL, created_at TEXT NOT NULL,
 last_used_at TEXT, last_verified_at TEXT, status TEXT NOT NULL, version INTEGER NOT NULL,
 friendly_name TEXT, device_reference TEXT, provider_reference TEXT);
CREATE TABLE IF NOT EXISTS novaid_authenticator_bindings(
 binding_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, identity_id TEXT NOT NULL,
 authenticator_id TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_attestation_records(
 attestation_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, credential_id TEXT NOT NULL,
 format TEXT NOT NULL, attestation_type TEXT NOT NULL, trust_path_metadata TEXT NOT NULL,
 verified_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_authenticator_status_history(
 transition_id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, credential_id TEXT NOT NULL,
 previous_status TEXT NOT NULL, new_status TEXT NOT NULL, reason_code TEXT NOT NULL,
 occurred_at TEXT NOT NULL, actor_identity_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_recovery_code_batches(
 batch_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,identity_id TEXT NOT NULL,status TEXT NOT NULL,
 created_at TEXT NOT NULL,expires_at TEXT NOT NULL,revoked_at TEXT,version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_recovery_codes(
 recovery_code_id TEXT PRIMARY KEY,batch_id TEXT NOT NULL,tenant_id TEXT NOT NULL,identity_id TEXT NOT NULL,
 code_hash TEXT NOT NULL UNIQUE,status TEXT NOT NULL,created_at TEXT NOT NULL,expires_at TEXT NOT NULL,
 used_at TEXT,revoked_at TEXT,attempt_count INTEGER NOT NULL DEFAULT 0,version INTEGER NOT NULL DEFAULT 1);
CREATE INDEX IF NOT EXISTS ix_novaid_recovery_codes_batch ON novaid_recovery_codes(batch_id,status);
CREATE TABLE IF NOT EXISTS novaid_account_recovery_requests(
 recovery_request_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,identity_id TEXT NOT NULL,status TEXT NOT NULL,
 recovery_method TEXT NOT NULL,requested_at TEXT NOT NULL,expires_at TEXT NOT NULL,approved_at TEXT,
 approved_by TEXT,completed_at TEXT,rejected_at TEXT,cancelled_at TEXT,reason TEXT NOT NULL,
 correlation_id TEXT NOT NULL,request_id TEXT NOT NULL,device_reference TEXT,network_reference TEXT,
 version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_account_recovery_approvals(
 approval_id TEXT PRIMARY KEY,recovery_request_id TEXT NOT NULL,tenant_id TEXT NOT NULL,
 approver_identity_id TEXT NOT NULL,decision TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL,
 expires_at TEXT NOT NULL,UNIQUE(recovery_request_id,approver_identity_id));
CREATE TABLE IF NOT EXISTS novaid_account_recovery_evidence(
 evidence_id TEXT PRIMARY KEY,recovery_request_id TEXT NOT NULL,tenant_id TEXT NOT NULL,
 identity_id TEXT NOT NULL,method TEXT NOT NULL,result TEXT NOT NULL,risk_indicators TEXT NOT NULL,
 actor_identity_id TEXT,correlation_id TEXT NOT NULL,request_id TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS novaid_tenant_webauthn_policies(
 tenant_id TEXT PRIMARY KEY,require_webauthn INTEGER NOT NULL,passkeys_enabled INTEGER NOT NULL,
 passwordless_enabled INTEGER NOT NULL,require_phishing_resistant_step_up INTEGER NOT NULL,
 user_verification TEXT NOT NULL,attestation TEXT NOT NULL,maximum_credentials INTEGER NOT NULL,
 recovery_codes_enabled INTEGER NOT NULL,recovery_code_count INTEGER NOT NULL,
 recovery_code_expiry_days INTEGER NOT NULL,recovery_approval_count INTEGER NOT NULL,
 recovery_requires_new_authenticator INTEGER NOT NULL,step_up_seconds INTEGER NOT NULL,
 updated_at TEXT NOT NULL,updated_by TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS novaid_tenant_webauthn_policy_history(
 policy_history_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,policy_version INTEGER NOT NULL,
 status TEXT NOT NULL,policy TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL,
 created_by TEXT NOT NULL,UNIQUE(tenant_id,policy_version));
CREATE TABLE IF NOT EXISTS novaid_webauthn_challenge_coordination(
 coordination_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,challenge_id TEXT NOT NULL,purpose TEXT NOT NULL,
 status TEXT NOT NULL,challenge_version INTEGER NOT NULL,created_at TEXT NOT NULL,expires_at TEXT NOT NULL,
 consumed_at TEXT,UNIQUE(tenant_id,challenge_id));
CREATE TABLE IF NOT EXISTS novaid_webauthn_outbox(
 outbox_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,event_type TEXT NOT NULL,resource_id TEXT NOT NULL,
 event_version INTEGER NOT NULL,payload TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,
 available_at TEXT NOT NULL,published_at TEXT,attempt_count INTEGER NOT NULL DEFAULT 0,
 version INTEGER NOT NULL DEFAULT 1,correlation_id TEXT NOT NULL DEFAULT '',
 request_id TEXT NOT NULL DEFAULT '',resource_type TEXT NOT NULL DEFAULT 'WEBAUTHN_CREDENTIAL',
 lease_owner TEXT,lease_expires_at TEXT,next_attempt_at TEXT,last_attempt_at TEXT,
 last_error TEXT,dead_letter_reason TEXT);
CREATE TABLE IF NOT EXISTS novaid_webauthn_event_checkpoints(
 consumer_name TEXT NOT NULL,tenant_id TEXT NOT NULL,event_version INTEGER NOT NULL,
 updated_at TEXT NOT NULL,resource_type TEXT NOT NULL DEFAULT '',resource_reference TEXT NOT NULL DEFAULT '',
 last_event_id TEXT,applied_at TEXT,PRIMARY KEY(consumer_name,tenant_id));
CREATE TABLE IF NOT EXISTS novaid_audit_replay_requests(
 replay_request_id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL,organization_id TEXT NOT NULL,environment_id TEXT NOT NULL DEFAULT '',
 requested_by TEXT NOT NULL,approved_by TEXT,executed_by TEXT,event_type_filters TEXT NOT NULL DEFAULT '[]',
 aggregate_filters TEXT NOT NULL DEFAULT '{}',subject_filters TEXT NOT NULL DEFAULT '{}',start_time TEXT,end_time TEXT,
 source_checkpoint TEXT,target_checkpoint TEXT,replay_mode TEXT NOT NULL,dry_run INTEGER NOT NULL DEFAULT 0,
 reason TEXT NOT NULL,risk_level TEXT NOT NULL,status TEXT NOT NULL,maximum_events INTEGER NOT NULL DEFAULT 100,
 created_at TEXT NOT NULL,approved_at TEXT,started_at TEXT,completed_at TEXT,cancelled_at TEXT,evidence_id TEXT,
 correlation_id TEXT NOT NULL,request_id TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS novaid_audit_replay_approvals(
 approval_id TEXT PRIMARY KEY,replay_request_id TEXT NOT NULL,tenant_id TEXT NOT NULL,organization_id TEXT NOT NULL,
 approver_id TEXT NOT NULL,decision TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL,
 UNIQUE(replay_request_id,approver_id,decision));
CREATE TABLE IF NOT EXISTS novaid_audit_replay_event_results(
 result_id TEXT PRIMARY KEY,replay_request_id TEXT NOT NULL,tenant_id TEXT NOT NULL,organization_id TEXT NOT NULL,
 event_id TEXT NOT NULL,event_type TEXT NOT NULL,decision TEXT NOT NULL,reason TEXT NOT NULL,created_at TEXT NOT NULL,
 UNIQUE(replay_request_id,event_id,decision));
"""


class NovaIDUnitOfWork(AbstractContextManager["NovaIDUnitOfWork"]):
    def __init__(self, path: str | Path = ":memory:") -> None:
        self.connection = sqlite3.connect(str(path), isolation_level=None, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        self.sessions = self

    def __enter__(self) -> "NovaIDUnitOfWork":
        self.connection.execute("BEGIN IMMEDIATE")
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> bool:
        if self.connection.in_transaction:
            self.connection.execute("ROLLBACK" if exc_type else "COMMIT")
        return False

    def create_tenant(self, tenant_id: str, name: str, now: datetime) -> None:
        self.connection.execute(
            "INSERT INTO novaid_tenants VALUES(?,?,?,?,?,1)",
            (tenant_id, name, "ACTIVE", now.isoformat(), now.isoformat()),
        )

    def lock_idempotency_key(self, tenant_id: str, key: str) -> None:
        # BEGIN IMMEDIATE already serializes the local test adapter's writers.
        del tenant_id, key

    def bump_identity_security_version(self, tenant_id: str, identity_id: str) -> None:
        result = self.connection.execute(
            "UPDATE novaid_identities SET security_version=security_version+1,version=version+1 "
            "WHERE identity_id=? AND tenant_id=?",
            (identity_id, tenant_id),
        )
        if result.rowcount != 1:
            raise RuntimeError("CONCURRENCY_CONFLICT")

    def _session_rows(self, query: str, parameters: tuple[Any, ...]) -> list[sqlite3.Row]:
        return list(self.connection.execute(query, parameters).fetchall())

    def list_sessions_for_identity(self, tenant_id: str, identity_id: str) -> list[sqlite3.Row]:
        return self._session_rows(
            "SELECT session_id,status,authentication_strength,created_at,last_seen_at,expires_at,"
            "authenticated_at,idle_expires_at,absolute_expires_at,pending_mfa_expires_at,"
            "step_up_expires_at,device_reference "
            "FROM novaid_authentication_sessions WHERE tenant_id=? AND identity_id=? "
            "ORDER BY created_at DESC",
            (tenant_id, identity_id),
        )

    def list_for_identity(self, tenant_id: str, identity_id: str) -> list[sqlite3.Row]:
        return [dict(row) for row in self.list_sessions_for_identity(tenant_id, identity_id)]

    def get_session_for_identity(
        self, tenant_id: str, identity_id: str, session_id: str
    ) -> sqlite3.Row | None:
        return self.connection.execute(
            "SELECT expires_at,status FROM novaid_authentication_sessions "
            "WHERE tenant_id=? AND identity_id=? AND session_id=?",
            (tenant_id, identity_id, session_id),
        ).fetchone()

    def get_for_identity(self, tenant_id: str, identity_id: str, session_id: str) -> sqlite3.Row | None:
        return self.get_session_for_identity(tenant_id, identity_id, session_id)

    def revoke_session(self, tenant_id: str, identity_id: str, session_id: str, reason: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='REVOKED',"
            "revoked_at=?,revocation_reason=? "
            "WHERE tenant_id=? AND identity_id=? AND session_id=?",
            (datetime.utcnow().isoformat(), reason, tenant_id, identity_id, session_id),
        )
        return result.rowcount

    def revoke(self, tenant_id: str, identity_id: str, session_id: str, reason: str) -> int:
        return self.revoke_session(tenant_id, identity_id, session_id, reason)

    def revoke_sessions_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> list[sqlite3.Row]:
        rows = self._session_rows(
            "SELECT session_id,expires_at FROM novaid_authentication_sessions "
            "WHERE tenant_id=? AND identity_id=? AND status NOT IN ('REVOKED','EXPIRED')",
            (tenant_id, identity_id),
        )
        self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='REVOKED',revoked_at=?,"
            "revocation_reason=? WHERE tenant_id=? AND identity_id=? "
            "AND status NOT IN ('REVOKED','EXPIRED')",
            (datetime.utcnow().isoformat(), reason, tenant_id, identity_id),
        )
        return rows

    def revoke_all_for_identity(self, tenant_id: str, identity_id: str, reason: str) -> list[sqlite3.Row]:
        return self.revoke_sessions_for_identity(tenant_id, identity_id, reason)

    def update_session_touch(
        self, tenant_id: str, identity_id: str, session_id: str, *, now: str
    ) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET last_seen_at=?,idle_expires_at=? "
            "WHERE tenant_id=? AND identity_id=? AND session_id=? AND status='ACTIVE'",
            (now, (datetime.fromisoformat(now) + timedelta(minutes=30)).isoformat(), tenant_id, identity_id, session_id),
        )
        return result.rowcount

    def touch(self, tenant_id: str, identity_id: str, session_id: str, *, now: str) -> int:
        return self.update_session_touch(tenant_id, identity_id, session_id, now=now)

    def update_session_step_up(
        self, tenant_id: str, identity_id: str, session_id: str, *, until: str
    ) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='STEP_UP_REQUIRED',"
            "step_up_expires_at=? WHERE tenant_id=? AND identity_id=? AND session_id=? "
            "AND status='ACTIVE'",
            (until, tenant_id, identity_id, session_id),
        )
        return result.rowcount

    def require_step_up(
        self, tenant_id: str, identity_id: str, session_id: str, *, until: str
    ) -> int:
        return self.update_session_step_up(tenant_id, identity_id, session_id, until=until)

    def complete_session_step_up(self, tenant_id: str, identity_id: str, session_id: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='ACTIVE',step_up_expires_at=NULL,"
            "authentication_strength='PASSWORD_OTP' WHERE tenant_id=? AND identity_id=? "
            "AND session_id=? AND status='STEP_UP_REQUIRED'",
            (tenant_id, identity_id, session_id),
        )
        return result.rowcount

    def complete_step_up(self, tenant_id: str, identity_id: str, session_id: str) -> int:
        return self.complete_session_step_up(tenant_id, identity_id, session_id)

    def lock_session(self, tenant_id: str, identity_id: str, session_id: str, *, locked_at: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='LOCKED',locked_at=? "
            "WHERE tenant_id=? AND identity_id=? AND session_id=? "
            "AND status IN ('ACTIVE','STEP_UP_REQUIRED')",
            (locked_at, tenant_id, identity_id, session_id),
        )
        return result.rowcount

    def unlock_session(self, tenant_id: str, identity_id: str, session_id: str) -> int:
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='ACTIVE',locked_at=NULL "
            "WHERE tenant_id=? AND identity_id=? AND session_id=? AND status='LOCKED'",
            (tenant_id, identity_id, session_id),
        )
        return result.rowcount

    def lock(self, tenant_id: str, identity_id: str, session_id: str, *, locked_at: str) -> int:
        return self.lock_session(tenant_id, identity_id, session_id, locked_at=locked_at)

    def unlock(self, tenant_id: str, identity_id: str, session_id: str) -> int:
        return self.unlock_session(tenant_id, identity_id, session_id)

    def expire_sessions(self, tenant_id: str, *, now: str) -> int:
        expired = 0
        rules = (
            ("PENDING_MFA", "pending_mfa_expires_at", "PENDING_MFA_EXPIRY"),
            ("ACTIVE", "idle_expires_at", "IDLE_EXPIRY"),
            ("STEP_UP_REQUIRED", "step_up_expires_at", "STEP_UP_EXPIRY"),
        )
        for status, column, reason in rules:
            result = self.connection.execute(
                f"UPDATE novaid_authentication_sessions SET status='EXPIRED',expired_at=?,"
                "revoked_at=?,revocation_reason=? WHERE tenant_id=? AND status=? "
                f"AND {column} IS NOT NULL AND {column}<=?",
                (now, now, reason, tenant_id, status, now),
            )
            expired += result.rowcount
        result = self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='EXPIRED',expired_at=?,"
            "revoked_at=?,revocation_reason='ABSOLUTE_EXPIRY' WHERE tenant_id=? "
            "AND status IN ('ACTIVE','PENDING_MFA','STEP_UP_REQUIRED','LOCKED') "
            "AND COALESCE(absolute_expires_at,expires_at)<=?",
            (now, now, tenant_id, now),
        )
        expired += result.rowcount
        return expired

    def expire_stale(self, tenant_id: str, *, now: str) -> int:
        return self.expire_sessions(tenant_id, now=now)

    def mark_session_compromised(
        self, tenant_id: str, identity_id: str, session_id: str, *, now: str
    ) -> sqlite3.Row | None:
        row = self.connection.execute(
            "SELECT expires_at FROM novaid_authentication_sessions "
            "WHERE tenant_id=? AND identity_id=? AND session_id=?",
            (tenant_id, identity_id, session_id),
        ).fetchone()
        if not row:
            return None
        self.connection.execute(
            "UPDATE novaid_authentication_sessions SET status='COMPROMISED',"
            "revoked_at=?,compromised_at=?,revocation_reason='SECURITY_CONTAINMENT',"
            "compromise_reason='SECURITY_CONTAINMENT' WHERE tenant_id=? AND identity_id=? "
            "AND session_id=? AND status NOT IN ('COMPROMISED','REVOKED','EXPIRED')",
            (now, now, tenant_id, identity_id, session_id),
        )
        self.connection.execute(
            "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=? "
            "WHERE tenant_id=? AND session_id=? AND status='ACTIVE'",
            (now, tenant_id, session_id),
        )
        return row

    def mark_compromised(
        self, tenant_id: str, identity_id: str, session_id: str, *, now: str
    ) -> sqlite3.Row | None:
        return self.mark_session_compromised(tenant_id, identity_id, session_id, now=now)

    def add_identity(self, identity: Identity) -> None:
        self.connection.execute(
            "INSERT INTO novaid_identities VALUES(?,?,?,?,?,?,?,?)",
            (
                identity.identity_id,
                identity.tenant_id,
                identity.normalized_email.lower(),
                identity.status,
                identity.created_at.isoformat(),
                identity.updated_at.isoformat(),
                identity.version,
                1,
            ),
        )

    def get_identity(self, context: RequestContext, identity_id: str) -> Identity:
        row = self.connection.execute(
            "SELECT * FROM novaid_identities WHERE identity_id=? AND tenant_id=?",
            (identity_id, context.tenant_id),
        ).fetchone()
        if row is None:
            raise LookupError("TENANT_ACCESS_DENIED")
        return Identity(
            row["identity_id"],
            row["tenant_id"],
            row["normalized_email"],
            IdentityStatus(row["status"]),
            datetime.fromisoformat(row["created_at"]),
            datetime.fromisoformat(row["updated_at"]),
            row["version"],
        )

    def update_identity(
        self, context: RequestContext, identity: Identity, expected_version: int
    ) -> None:
        result = self.connection.execute(
            "UPDATE novaid_identities SET status=?,updated_at=?,version=? WHERE identity_id=? AND tenant_id=? AND version=?",
            (
                identity.status,
                identity.updated_at.isoformat(),
                identity.version,
                identity.identity_id,
                context.tenant_id,
                expected_version,
            ),
        )
        if result.rowcount != 1:
            raise RuntimeError("CONCURRENCY_CONFLICT")

    def add_event(self, event: SecurityEvent) -> None:
        forbidden = {
            "password",
            "otp",
            "access_token",
            "refresh_token",
            "private_key",
            "recovery_secret",
        }
        if forbidden & {key.lower() for key in event.metadata}:
            raise ValueError("SECRET_IN_SECURITY_EVENT")
        self.connection.execute(
            "INSERT INTO novaid_security_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                event.event_id,
                event.event_type,
                event.severity,
                event.tenant_id,
                event.actor_identity_id,
                event.subject_identity_id,
                event.correlation_id,
                event.request_id,
                event.occurred_at.isoformat(),
                event.recorded_at.isoformat(),
                event.outcome,
                json.dumps(event.reason_codes),
                json.dumps(event.metadata),
                event.schema_version,
            ),
        )

    def count(self, table: str) -> int:
        allowed = {
            row[0]
            for row in self.connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if table not in allowed:
            raise ValueError("invalid_table")
        return int(self.connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
