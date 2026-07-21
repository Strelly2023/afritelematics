from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets
from uuid import uuid4

from ..persistence import NovaIDUnitOfWork
from ..revocation import RevocationStore
from ..security import PasswordHasher


def _id() -> str:
    return str(uuid4())


@dataclass(frozen=True)
class PasswordPolicy:
    minimum_length: int = 12
    maximum_length: int = 1024
    history_depth: int = 5

    def validate(self, password: str) -> None:
        if not self.minimum_length <= len(password) <= self.maximum_length:
            raise ValueError("PASSWORD_POLICY_REJECTED")


class PasswordLifecycleService:
    def __init__(
        self,
        uow: NovaIDUnitOfWork,
        revocations: RevocationStore,
        *,
        pepper: bytes,
        policy: PasswordPolicy | None = None,
        outbox=None,
    ) -> None:
        self.uow, self.revocations, self.pepper = uow, revocations, pepper
        self.policy, self.hasher = policy or PasswordPolicy(), PasswordHasher()
        self.outbox = outbox

    def _otp_hash(self, value: str) -> str:
        return hmac.new(self.pepper, f"password-reset:{value}".encode(), hashlib.sha256).hexdigest()

    def _credentials(self, tenant: str, identity: str):
        return self.uow.list_password_credentials(tenant, identity)

    def _reject_reuse(self, tenant: str, identity: str, password: str) -> None:
        for row in self._credentials(tenant, identity)[: self.policy.history_depth]:
            if self.hasher.verify(password, row["password_hash"]):
                raise ValueError("PASSWORD_REUSE_REJECTED")

    def _replace(self, tenant: str, identity: str, password: str) -> None:
        now, credential = datetime.now(UTC).isoformat(), _id()
        self.uow.supersede_active_password_credentials(tenant, identity, now=now)
        self.uow.insert_password_credential(
            credential,
            tenant,
            identity,
            self.hasher.hash(password),
            "scrypt-v1",
            now=now,
        )
        self.uow.bump_identity_security_version(tenant, identity)

    def change(
        self,
        *,
        tenant_id: str,
        identity_id: str,
        session_id: str,
        current_password: str,
        new_password: str,
    ) -> None:
        self.policy.validate(new_password)
        with self.uow:
            session = self.uow.sessions.get_active_strength(tenant_id, identity_id, session_id)
            active = next(
                (
                    row
                    for row in self._credentials(tenant_id, identity_id)
                    if row["status"] == "ACTIVE"
                ),
                None,
            )
            if not session or session["authentication_strength"] != "PASSWORD_OTP" or not active:
                raise ValueError("AUTHENTICATION_DENIED")
            if not self.hasher.verify(current_password, active["password_hash"]):
                raise ValueError("AUTHENTICATION_DENIED")
            self._reject_reuse(tenant_id, identity_id, new_password)
            self._replace(tenant_id, identity_id, new_password)
            self._revoke_all(tenant_id, identity_id, "PASSWORD_CHANGED")

    def request_reset(self, *, tenant_id: str, email: str, correlation_id: str) -> dict[str, str]:
        response = {"status": "ACCEPTED"}
        with self.uow:
            row = self.uow.identities.get_by_email(tenant_id, email.strip().lower())
            if not row:
                return response
            code, challenge, now = f"{secrets.randbelow(1_000_000):06d}", _id(), datetime.now(UTC)
            self.uow.create_otp_challenge(
                challenge,
                tenant_id,
                row["identity_id"],
                "PASSWORD_RESET",
                "reset-ref",
                self._otp_hash(code),
                now.isoformat(),
                (now + timedelta(minutes=5)).isoformat(),
                5,
                "PENDING",
                correlation_id,
            )
            response.update({"challenge_id": challenge, "reset_code": code})
        return response

    def complete_reset(
        self, *, tenant_id: str, challenge_id: str, code: str, new_password: str
    ) -> str:
        self.policy.validate(new_password)
        with self.uow:
            row = self.uow.get_otp_challenge(tenant_id, challenge_id)
            if not row or row["purpose"] != "PASSWORD_RESET" or row["status"] != "PENDING":
                raise ValueError("PASSWORD_RESET_REJECTED")
            if datetime.fromisoformat(row["expires_at"]) <= datetime.now(UTC):
                raise ValueError("PASSWORD_RESET_REJECTED")
            if not hmac.compare_digest(row["secret_hash"], self._otp_hash(code)):
                self.uow.increment_otp_challenge_attempt(challenge_id)
                raise ValueError("PASSWORD_RESET_REJECTED")
            self._reject_reuse(tenant_id, row["identity_id"], new_password)
            if self.uow.consume_otp_challenge(challenge_id, now=datetime.now(UTC).isoformat()) != 1:
                raise ValueError("PASSWORD_RESET_REJECTED")
            self._replace(tenant_id, row["identity_id"], new_password)
            self._revoke_all(tenant_id, row["identity_id"], "PASSWORD_RESET")
            return row["identity_id"]

    def _revoke_all(self, tenant: str, identity: str, reason: str) -> None:
        now = datetime.now(UTC).isoformat()
        self.uow.sessions.revoke_sessions_for_identity(tenant, identity, reason)
        self.uow.revoke_refresh_families_for_identity(tenant, identity, reason)
        if self.outbox:
            self.outbox.enqueue(
                tenant_id=tenant,
                event_type="TOKEN_FAMILY_REVOKED",
                resource_type="IDENTITY",
                resource_id=identity,
                event_version=1,
                payload={"reason": reason},
            )
