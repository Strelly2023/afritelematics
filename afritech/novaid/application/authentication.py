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
        self.uow.record_security_event(
            type(
                "SecurityEventRecord",
                (),
                {
                    "event_id": _id(),
                    "event_type": event_type,
                    "severity": "HIGH" if "REPLAY" in event_type else "INFO",
                    "tenant_id": tenant,
                    "actor_identity_id": actor,
                    "subject_identity_id": subject,
                    "correlation_id": correlation,
                    "request_id": request,
                    "occurred_at": now,
                    "recorded_at": now,
                    "outcome": outcome,
                    "reason_codes": [],
                    "metadata": {},
                    "schema_version": 1,
                },
            )()
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
            prior = self.uow.get_idempotency_record(tenant_id, idempotency_key)
            if prior:
                if not hmac.compare_digest(prior["payload_hash"], payload_hash):
                    raise AuthenticationError("IDEMPOTENCY_CONFLICT")
                return json.loads(prior["response_json"])
            tenant = self.uow.get_tenant_status(tenant_id)
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
            self.uow.create_registration_membership(
                membership_id, tenant_id, identity_id, now=now.isoformat()
            )
            self.uow.insert_password_credential(
                credential_id,
                tenant_id,
                identity_id,
                self.hasher.hash(password),
                "scrypt-v1",
                now=now.isoformat(),
            )
            otp = f"{secrets.randbelow(1_000_000):06d}"
            self.uow.create_registration_challenge(
                challenge_id,
                tenant_id,
                identity_id,
                "EMAIL_VERIFICATION",
                "email-ref",
                self._hash("otp", otp),
                now.isoformat(),
                (now + timedelta(minutes=5)).isoformat(),
                5,
                correlation_id,
            )
            response = {
                "identity_id": identity_id,
                "membership_id": membership_id,
                "challenge_id": challenge_id,
                "verification_code": otp,
            }
            self.uow.insert_idempotency_record(
                tenant_id, idempotency_key, payload_hash, json.dumps(response), now=now.isoformat()
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
            challenge = self.uow.get_otp_challenge(tenant_id, challenge_id)
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
                status = "ATTEMPTS_EXCEEDED" if attempts >= challenge["maximum_attempts"] else "PENDING"
                self.uow.increment_otp_challenge_attempt(challenge_id)
                if status != "PENDING":
                    self.uow.update_otp_status(challenge_id, status)
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
            if self.uow.consume_otp_challenge(challenge_id, now=now.isoformat()) != 1:
                raise AuthenticationError("OTP_INVALID")
            identity = self.uow.get_identity_for_tenant(tenant_id, identity_id)
            if not identity or identity["status"] != "PENDING_VERIFICATION":
                raise AuthenticationError("AUTHENTICATION_DENIED")
            self.uow.activate_identity(tenant_id, identity_id, now=now.isoformat())
            for event in ("OTP_VERIFIED", "IDENTITY_ACTIVATED", "IDENTITY_VERIFICATION_COMPLETED"):
                self._event(event, tenant_id, identity_id, identity_id, correlation_id, request_id)

    def authenticate(
        self, *, tenant_id: str, email: str, password: str, correlation_id: str, request_id: str
    ) -> dict[str, str]:
        if self.lockout and self.lockout.is_locked(tenant_id, email):
            raise AuthenticationError("INVALID_CREDENTIALS")
        with self.uow:
            row = self.uow.get_login_identity(tenant_id, email.strip().lower())
            if (
                not row
                or row["status"] != "ACTIVE"
                or not self.hasher.verify(password, row["password_hash"])
            ):
                if self.lockout:
                    self.lockout.record_failure(tenant_id, email)
                raise AuthenticationError("INVALID_CREDENTIALS")
            if self.lockout:
                self.lockout.reset(tenant_id, email)
            now, session_id, challenge_id = _now(), _id(), _id()
            self.uow.create_authentication_session(
                session_id,
                tenant_id,
                row["identity_id"],
                now.isoformat(),
                "PASSWORD",
                row["credential_id"],
                0.1,
                row["membership_id"],
                created_at=now.isoformat(),
                expires_at=(now + timedelta(hours=12)).isoformat(),
                pending_mfa_expires_at=(now + timedelta(minutes=5)).isoformat(),
                authentication_methods='["PASSWORD"]',
            )
            otp = f"{secrets.randbelow(1_000_000):06d}"
            self.uow.create_login_challenge(
                challenge_id,
                tenant_id,
                row["identity_id"],
                session_id,
                self._hash("otp", otp),
                now.isoformat(),
                (now + timedelta(minutes=5)).isoformat(),
                correlation_id,
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
            row = self.uow.get_mfa_challenge_session(tenant_id, challenge_id, session_id)
            if (
                not row
                or row["status"] != "PENDING"
                or row["session_status"] != "PENDING_MFA"
                or not hmac.compare_digest(row["secret_hash"], self._hash("otp", code))
            ):
                raise AuthenticationError("OTP_INVALID")
            now = _now()
            self.uow.consume_otp_challenge(challenge_id, now=now.isoformat())
            self.uow.activate_session_and_refresh(
                session_id, now=now.isoformat(), authentication_methods='["PASSWORD","OTP"]'
            )
            family_id, token_id, refresh = _id(), _id(), secrets.token_urlsafe(48)
            self.uow.create_refresh_family(
                family_id,
                session_id,
                row["identity_id"],
                tenant_id,
                created_at=now.isoformat(),
                expires_at=(now + timedelta(days=30)).isoformat(),
            )
            self.uow.create_refresh_token(
                token_id,
                family_id,
                session_id,
                row["identity_id"],
                tenant_id,
                self._hash("refresh", refresh),
                None,
                issued_at=now.isoformat(),
                expires_at=(now + timedelta(days=7)).isoformat(),
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
            session = self.uow.get_pending_session(tenant_id, session_id)
            now = _now()
            if (
                not session
                or session["status"] != "PENDING_MFA"
                or datetime.fromisoformat(session["expires_at"]) <= now
            ):
                raise AuthenticationError("AUTHENTICATION_DENIED")
            prior = self.uow.get_recent_login_challenge(tenant_id, session["identity_id"], session_id)
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
                self.uow.supersede_challenge(prior["challenge_id"])
                self._event(
                    "MFA_CHALLENGE_SUPERSEDED",
                    tenant_id,
                    session["identity_id"],
                    session["identity_id"],
                    correlation_id,
                    request_id,
                )
            challenge_id, otp = _id(), f"{secrets.randbelow(1_000_000):06d}"
            self.uow.create_login_challenge(
                challenge_id,
                tenant_id,
                session["identity_id"],
                session_id,
                self._hash("otp", otp),
                now.isoformat(),
                (now + timedelta(minutes=5)).isoformat(),
                correlation_id,
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
            row = self.uow.get_refresh_context(tenant_id, token_id)
            if not row or not hmac.compare_digest(row["token_hash"], self._hash("refresh", raw)):
                raise AuthenticationError("INVALID_CREDENTIALS")
            if row["status"] == "USED":
                now = _now().isoformat()
                self.uow.mark_refresh_replayed(token_id)
                self.uow.revoke_refresh_family(row["family_id"], now=now)
                self.uow.revoke_refresh_session(row["session_id"], now=now, reason="TOKEN_REPLAY")
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
                self.uow.expire_refresh_session(
                    tenant_id, row["session_id"], now=_now().isoformat(), reason="ON_REFRESH_EXPIRY"
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
                if self.uow.mark_refresh_used(token_id, successor_id, now=now.isoformat()) != 1:
                    raise AuthenticationError("CONCURRENCY_CONFLICT")
                self.uow.create_refresh_token(
                    successor_id,
                    row["family_id"],
                    row["session_id"],
                    row["identity_id"],
                    tenant_id,
                    self._hash("refresh", successor),
                    token_id,
                    issued_at=now.isoformat(),
                    expires_at=row["expires_at"],
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
