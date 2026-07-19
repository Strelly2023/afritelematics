"""Durable, tenant-bound NovaID registration and authentication flow."""
# ruff: noqa: E501 -- explicit security SQL remains visible at call sites.

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
import secrets
from uuid import uuid4
from typing import TYPE_CHECKING

from ..domain import Identity
from ..persistence import NovaIDUnitOfWork
from ..security import PasswordHasher

if TYPE_CHECKING:
    from .lockout import AuthenticationLockoutService


def _now() -> datetime:
    return datetime.now(UTC)


def _id() -> str:
    return str(uuid4())


class AuthenticationError(ValueError):
    """Stable public failure with no identity-enumeration detail."""


class DurableAuthenticationService:
    def __init__(
        self,
        uow: NovaIDUnitOfWork,
        *,
        pepper: bytes,
        hasher: PasswordHasher | None = None,
        lockout: "AuthenticationLockoutService | None" = None,
    ) -> None:
        if len(pepper) < 32:
            raise ValueError("token_pepper_too_short")
        self.uow, self.pepper = uow, pepper
        self.hasher = hasher or PasswordHasher()
        self.lockout = lockout

    def _hash(self, purpose: str, value: str) -> str:
        return hmac.new(self.pepper, f"{purpose}:{value}".encode(), hashlib.sha256).hexdigest()

    def _event(
        self,
        event_type: str,
        tenant: str,
        actor: str,
        subject: str,
        correlation: str,
        request: str,
        outcome: str = "SUCCESS",
    ) -> None:
        now = _now().isoformat()
        self.uow.connection.execute(
            "INSERT INTO novaid_security_events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
            (
                _id(),
                event_type,
                "HIGH" if "REPLAY" in event_type else "INFO",
                tenant,
                actor,
                subject,
                correlation,
                request,
                now,
                now,
                outcome,
                "[]",
                "{}",
            ),
        )

    def register(
        self,
        *,
        tenant_id: str,
        email: str,
        password: str,
        idempotency_key: str,
        correlation_id: str,
        request_id: str,
    ) -> dict[str, str]:
        normalized = email.strip().lower()
        payload_hash = self._hash("registration", f"{normalized}:{password}")
        with self.uow:
            self.uow.lock_idempotency_key(tenant_id, idempotency_key)
            prior = self.uow.connection.execute(
                "SELECT payload_hash,response_json FROM novaid_idempotency_records WHERE tenant_id=? AND idempotency_key=?",
                (tenant_id, idempotency_key),
            ).fetchone()
            if prior:
                if not hmac.compare_digest(prior["payload_hash"], payload_hash):
                    raise AuthenticationError("IDEMPOTENCY_CONFLICT")
                return json.loads(prior["response_json"])
            tenant = self.uow.connection.execute(
                "SELECT status FROM novaid_tenants WHERE tenant_id=?", (tenant_id,)
            ).fetchone()
            if not tenant or tenant["status"] != "ACTIVE":
                raise AuthenticationError("AUTHENTICATION_DENIED")
            now, identity_id, membership_id, credential_id, challenge_id = (
                _now(),
                _id(),
                _id(),
                _id(),
                _id(),
            )
            identity = Identity(identity_id, tenant_id, normalized)
            self.uow.add_identity(identity)
            self.uow.connection.execute(
                "INSERT INTO novaid_tenant_memberships VALUES(?,?,?,?,?,?,?,?)",
                (
                    membership_id,
                    tenant_id,
                    identity_id,
                    "MEMBER",
                    "ACTIVE",
                    now.isoformat(),
                    now.isoformat(),
                    1,
                ),
            )
            self.uow.connection.execute(
                "INSERT INTO novaid_credentials VALUES(?,?,?,?,?,?,?,?)",
                (
                    credential_id,
                    tenant_id,
                    identity_id,
                    "PASSWORD",
                    "ACTIVE",
                    now.isoformat(),
                    now.isoformat(),
                    1,
                ),
            )
            self.uow.connection.execute(
                "INSERT INTO novaid_password_credentials VALUES(?,?,?,?,?)",
                (credential_id, self.hasher.hash(password), "scrypt-v1", None, None),
            )
            otp = f"{secrets.randbelow(1_000_000):06d}"
            self.uow.connection.execute(
                "INSERT INTO novaid_otp_challenges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    challenge_id,
                    tenant_id,
                    identity_id,
                    "EMAIL_VERIFICATION",
                    "email-ref",
                    self._hash("otp", otp),
                    now.isoformat(),
                    (now + timedelta(minutes=5)).isoformat(),
                    None,
                    0,
                    5,
                    "PENDING",
                    correlation_id,
                ),
            )
            response = {
                "identity_id": identity_id,
                "membership_id": membership_id,
                "challenge_id": challenge_id,
                "verification_code": otp,
            }
            self.uow.connection.execute(
                "INSERT INTO novaid_idempotency_records VALUES(?,?,?,?,?)",
                (tenant_id, idempotency_key, payload_hash, json.dumps(response), now.isoformat()),
            )
            for event in (
                "IDENTITY_CREATED",
                "TENANT_MEMBERSHIP_CREATED",
                "PASSWORD_CREATED",
                "OTP_ISSUED",
                "REGISTRATION_INITIATED",
            ):
                self._event(event, tenant_id, identity_id, identity_id, correlation_id, request_id)
            return response

    def verify_identity(
        self,
        *,
        tenant_id: str,
        identity_id: str,
        challenge_id: str,
        code: str,
        correlation_id: str,
        request_id: str,
    ) -> None:
        with self.uow:
            challenge = self.uow.connection.execute(
                "SELECT * FROM novaid_otp_challenges WHERE challenge_id=? AND tenant_id=? AND identity_id=?",
                (challenge_id, tenant_id, identity_id),
            ).fetchone()
            if not challenge or challenge["purpose"] != "EMAIL_VERIFICATION":
                raise AuthenticationError("OTP_INVALID")
            now = _now()
            if (
                challenge["status"] != "PENDING"
                or datetime.fromisoformat(challenge["expires_at"]) <= now
            ):
                raise AuthenticationError("OTP_EXPIRED")
            if not hmac.compare_digest(challenge["secret_hash"], self._hash("otp", code)):
                attempts = challenge["attempt_count"] + 1
                status = (
                    "ATTEMPTS_EXCEEDED" if attempts >= challenge["maximum_attempts"] else "PENDING"
                )
                self.uow.connection.execute(
                    "UPDATE novaid_otp_challenges SET attempt_count=?,status=? WHERE challenge_id=?",
                    (attempts, status, challenge_id),
                )
                self._event(
                    "OTP_REJECTED",
                    tenant_id,
                    identity_id,
                    identity_id,
                    correlation_id,
                    request_id,
                    "DENIED",
                )
                raise AuthenticationError("OTP_INVALID")
            updated = self.uow.connection.execute(
                "UPDATE novaid_otp_challenges SET consumed_at=?,status='CONSUMED' WHERE challenge_id=? AND status='PENDING'",
                (now.isoformat(), challenge_id),
            )
            if updated.rowcount != 1:
                raise AuthenticationError("OTP_INVALID")
            identity = self.uow.connection.execute(
                "SELECT version,status FROM novaid_identities WHERE identity_id=? AND tenant_id=?",
                (identity_id, tenant_id),
            ).fetchone()
            if not identity or identity["status"] != "PENDING_VERIFICATION":
                raise AuthenticationError("AUTHENTICATION_DENIED")
            self.uow.connection.execute(
                "UPDATE novaid_identities SET status='ACTIVE',updated_at=?,version=version+1 WHERE identity_id=?",
                (now.isoformat(), identity_id),
            )
            for event in ("OTP_VERIFIED", "IDENTITY_ACTIVATED", "IDENTITY_VERIFICATION_COMPLETED"):
                self._event(event, tenant_id, identity_id, identity_id, correlation_id, request_id)

    def authenticate(
        self, *, tenant_id: str, email: str, password: str, correlation_id: str, request_id: str
    ) -> dict[str, str]:
        if self.lockout and self.lockout.is_locked(tenant_id, email):
            raise AuthenticationError("INVALID_CREDENTIALS")
        with self.uow:
            row = self.uow.connection.execute(
                "SELECT i.identity_id,i.status,m.membership_id,c.credential_id,p.password_hash "
                "FROM novaid_identities i JOIN novaid_tenant_memberships m ON m.identity_id=i.identity_id AND m.tenant_id=i.tenant_id "
                "JOIN novaid_credentials c ON c.identity_id=i.identity_id AND c.tenant_id=i.tenant_id "
                "JOIN novaid_password_credentials p ON p.credential_id=c.credential_id "
                "WHERE i.tenant_id=? AND i.normalized_email=? AND m.status='ACTIVE' AND c.status='ACTIVE'",
                (tenant_id, email.strip().lower()),
            ).fetchone()
            if (
                not row
                or row["status"] != "ACTIVE"
                or not self.hasher.verify(password, row["password_hash"])
            ):
                if self.lockout:
                    self.lockout.record_failure(tenant_id, email)
                    self.uow.connection.execute("COMMIT")
                raise AuthenticationError("INVALID_CREDENTIALS")
            if self.lockout:
                self.lockout.reset(tenant_id, email)
            now, session_id, challenge_id = _now(), _id(), _id()
            self.uow.connection.execute(
                "INSERT INTO novaid_authentication_sessions(session_id,tenant_id,identity_id,"
                "authentication_time,authentication_strength,credential_id,device_reference,"
                "client_reference,risk_score,status,created_at,last_seen_at,expires_at,revoked_at,"
                "revocation_reason,version,membership_id,authenticated_at,idle_expires_at,"
                "absolute_expires_at,pending_mfa_expires_at,authentication_methods,security_version) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    session_id,
                    tenant_id,
                    row["identity_id"],
                    now.isoformat(),
                    "PASSWORD",
                    row["credential_id"],
                    None,
                    None,
                    0.1,
                    "PENDING_MFA",
                    now.isoformat(),
                    now.isoformat(),
                    (now + timedelta(hours=12)).isoformat(),
                    None,
                    None,
                    1,
                    row["membership_id"],
                    None,
                    (now + timedelta(minutes=30)).isoformat(),
                    (now + timedelta(hours=12)).isoformat(),
                    (now + timedelta(minutes=5)).isoformat(),
                    '["PASSWORD"]',
                    1,
                ),
            )
            otp = f"{secrets.randbelow(1_000_000):06d}"
            self.uow.connection.execute(
                "INSERT INTO novaid_otp_challenges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    challenge_id,
                    tenant_id,
                    row["identity_id"],
                    "LOGIN",
                    session_id,
                    self._hash("otp", otp),
                    now.isoformat(),
                    (now + timedelta(minutes=5)).isoformat(),
                    None,
                    0,
                    5,
                    "PENDING",
                    correlation_id,
                ),
            )
            self._event(
                "MFA_CHALLENGE_CREATED",
                tenant_id,
                row["identity_id"],
                row["identity_id"],
                correlation_id,
                request_id,
            )
            return {
                "outcome": "MFA_REQUIRED",
                "session_id": session_id,
                "challenge_id": challenge_id,
                "mfa_code": otp,
            }

    def complete_mfa(
        self,
        *,
        tenant_id: str,
        session_id: str,
        challenge_id: str,
        code: str,
        correlation_id: str,
        request_id: str,
    ) -> dict[str, str]:
        with self.uow:
            row = self.uow.connection.execute(
                "SELECT c.*,s.identity_id,s.status session_status FROM novaid_otp_challenges c "
                "JOIN novaid_authentication_sessions s "
                "ON CAST(s.session_id AS TEXT)=c.destination_reference "
                "WHERE c.challenge_id=? AND c.tenant_id=? AND s.session_id=?",
                (challenge_id, tenant_id, session_id),
            ).fetchone()
            if (
                not row
                or row["status"] != "PENDING"
                or row["session_status"] != "PENDING_MFA"
                or not hmac.compare_digest(row["secret_hash"], self._hash("otp", code))
            ):
                raise AuthenticationError("OTP_INVALID")
            now = _now()
            self.uow.connection.execute(
                "UPDATE novaid_otp_challenges SET status='CONSUMED',consumed_at=? WHERE challenge_id=?",
                (now.isoformat(), challenge_id),
            )
            self.uow.connection.execute(
                "UPDATE novaid_authentication_sessions SET status='ACTIVE',"
                "authentication_strength='PASSWORD_OTP',authenticated_at=?,"
                'authentication_methods=\'["PASSWORD","OTP"]\',pending_mfa_expires_at=NULL '
                "WHERE session_id=?",
                (now.isoformat(), session_id),
            )
            family_id, token_id, refresh = _id(), _id(), secrets.token_urlsafe(48)
            self.uow.connection.execute(
                "INSERT INTO novaid_refresh_token_families VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    family_id,
                    session_id,
                    row["identity_id"],
                    tenant_id,
                    "ACTIVE",
                    now.isoformat(),
                    (now + timedelta(days=30)).isoformat(),
                    None,
                    1,
                ),
            )
            self.uow.connection.execute(
                "INSERT INTO novaid_refresh_tokens VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    token_id,
                    family_id,
                    session_id,
                    row["identity_id"],
                    tenant_id,
                    self._hash("refresh", refresh),
                    None,
                    now.isoformat(),
                    (now + timedelta(days=7)).isoformat(),
                    None,
                    None,
                    None,
                    "ACTIVE",
                ),
            )
            self._event(
                "SESSION_ACTIVATED",
                tenant_id,
                row["identity_id"],
                row["identity_id"],
                correlation_id,
                request_id,
            )
            self._event(
                "REFRESH_TOKEN_ISSUED",
                tenant_id,
                row["identity_id"],
                row["identity_id"],
                correlation_id,
                request_id,
            )
            return {"session_id": session_id, "refresh_token": f"{token_id}.{refresh}"}

    def issue_mfa_challenge(
        self,
        *,
        tenant_id: str,
        session_id: str,
        correlation_id: str,
        request_id: str,
    ) -> dict[str, str]:
        """Replace the pending login OTP, subject to a short resend cooldown."""
        with self.uow:
            session = self.uow.connection.execute(
                "SELECT identity_id,status,expires_at FROM novaid_authentication_sessions "
                "WHERE tenant_id=? AND session_id=?",
                (tenant_id, session_id),
            ).fetchone()
            now = _now()
            if (
                not session
                or session["status"] != "PENDING_MFA"
                or datetime.fromisoformat(session["expires_at"]) <= now
            ):
                raise AuthenticationError("AUTHENTICATION_DENIED")
            prior = self.uow.connection.execute(
                "SELECT challenge_id,created_at FROM novaid_otp_challenges "
                "WHERE tenant_id=? AND identity_id=? AND purpose='LOGIN' "
                "AND destination_reference=? AND status='PENDING' "
                "ORDER BY created_at DESC LIMIT 1",
                (tenant_id, session["identity_id"], session_id),
            ).fetchone()
            if prior and now - datetime.fromisoformat(prior["created_at"]) < timedelta(seconds=30):
                self._event(
                    "MFA_CHALLENGE_REJECTED",
                    tenant_id,
                    session["identity_id"],
                    session["identity_id"],
                    correlation_id,
                    request_id,
                    "DENIED",
                )
                raise AuthenticationError("AUTHENTICATION_DENIED")
            if prior:
                self.uow.connection.execute(
                    "UPDATE novaid_otp_challenges SET status='SUPERSEDED' WHERE challenge_id=?",
                    (prior["challenge_id"],),
                )
                self._event(
                    "MFA_CHALLENGE_SUPERSEDED",
                    tenant_id,
                    session["identity_id"],
                    session["identity_id"],
                    correlation_id,
                    request_id,
                )
            challenge_id, otp = _id(), f"{secrets.randbelow(1_000_000):06d}"
            self.uow.connection.execute(
                "INSERT INTO novaid_otp_challenges VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    challenge_id,
                    tenant_id,
                    session["identity_id"],
                    "LOGIN",
                    session_id,
                    self._hash("otp", otp),
                    now.isoformat(),
                    (now + timedelta(minutes=5)).isoformat(),
                    None,
                    0,
                    5,
                    "PENDING",
                    correlation_id,
                ),
            )
            self._event(
                "MFA_CHALLENGE_RESENT",
                tenant_id,
                session["identity_id"],
                session["identity_id"],
                correlation_id,
                request_id,
            )
            return {"session_id": session_id, "challenge_id": challenge_id, "mfa_code": otp}

    def refresh(
        self, *, tenant_id: str, presented_token: str, correlation_id: str, request_id: str
    ) -> str:
        try:
            token_id, raw = presented_token.split(".", 1)
        except ValueError as exc:
            raise AuthenticationError("INVALID_CREDENTIALS") from exc
        replay_detected = False
        replacement = ""
        with self.uow:
            row = self.uow.connection.execute(
                "SELECT t.*,f.status family_status,s.status session_status,"
                "s.idle_expires_at,s.absolute_expires_at,s.expires_at session_expires_at "
                "FROM novaid_refresh_tokens t "
                "JOIN novaid_refresh_token_families f ON f.family_id=t.family_id "
                "JOIN novaid_authentication_sessions s ON s.session_id=t.session_id "
                "WHERE t.token_id=? AND t.tenant_id=?",
                (token_id, tenant_id),
            ).fetchone()
            if not row or not hmac.compare_digest(row["token_hash"], self._hash("refresh", raw)):
                raise AuthenticationError("INVALID_CREDENTIALS")
            if row["status"] == "USED":
                now = _now().isoformat()
                self.uow.connection.execute(
                    "UPDATE novaid_refresh_tokens SET status='REPLAYED' WHERE token_id=?",
                    (token_id,),
                )
                self.uow.connection.execute(
                    "UPDATE novaid_refresh_token_families SET status='REVOKED',revoked_at=? WHERE family_id=?",
                    (now, row["family_id"]),
                )
                self.uow.connection.execute(
                    "UPDATE novaid_authentication_sessions SET status='REVOKED',revoked_at=?,revocation_reason='TOKEN_REPLAY' WHERE session_id=?",
                    (now, row["session_id"]),
                )
                self._event(
                    "REFRESH_TOKEN_REPLAY_DETECTED",
                    tenant_id,
                    row["identity_id"],
                    row["identity_id"],
                    correlation_id,
                    request_id,
                    "DENIED",
                )
                replay_detected = True
            elif any(
                value and datetime.fromisoformat(value) <= _now()
                for value in (
                    row["idle_expires_at"],
                    row["absolute_expires_at"] or row["session_expires_at"],
                )
            ):
                self.uow.connection.execute(
                    "UPDATE novaid_authentication_sessions SET status='EXPIRED',expired_at=?,"
                    "revoked_at=?,revocation_reason='ON_REFRESH_EXPIRY' WHERE tenant_id=? "
                    "AND session_id=? AND status='ACTIVE'",
                    (_now().isoformat(), _now().isoformat(), tenant_id, row["session_id"]),
                )
                raise AuthenticationError("SESSION_REVOKED")
            elif (
                row["status"] != "ACTIVE"
                or row["family_status"] != "ACTIVE"
                or row["session_status"] != "ACTIVE"
            ):
                raise AuthenticationError("SESSION_REVOKED")
            else:
                now, successor_id, successor = _now(), _id(), secrets.token_urlsafe(48)
                changed = self.uow.connection.execute(
                    "UPDATE novaid_refresh_tokens SET status='USED',used_at=?,replacement_token_id=? WHERE token_id=? AND status='ACTIVE'",
                    (now.isoformat(), successor_id, token_id),
                )
                if changed.rowcount != 1:
                    raise AuthenticationError("CONCURRENCY_CONFLICT")
                self.uow.connection.execute(
                    "INSERT INTO novaid_refresh_tokens VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        successor_id,
                        row["family_id"],
                        row["session_id"],
                        row["identity_id"],
                        tenant_id,
                        self._hash("refresh", successor),
                        token_id,
                        now.isoformat(),
                        row["expires_at"],
                        None,
                        None,
                        None,
                        "ACTIVE",
                    ),
                )
                self._event(
                    "REFRESH_TOKEN_ROTATED",
                    tenant_id,
                    row["identity_id"],
                    row["identity_id"],
                    correlation_id,
                    request_id,
                )
                replacement = f"{successor_id}.{successor}"
        if replay_detected:
            raise AuthenticationError("TOKEN_REPLAY_DETECTED")
        return replacement
