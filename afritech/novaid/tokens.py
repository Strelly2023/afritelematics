"""Short-lived access tokens bound to durable NovaID security state."""
# ruff: noqa: E501 -- explicit token validation queries remain visible.

from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import json
from uuid import uuid4

from .persistence import NovaIDUnitOfWork
from .revocation import RevocationStore


def _encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


class AccessTokenError(ValueError):
    pass


class AccessTokenService:
    def __init__(
        self,
        uow: NovaIDUnitOfWork,
        revocations: RevocationStore,
        *,
        signing_key: bytes,
        issuer: str,
        audience: str,
        lifetime_seconds: int = 900,
    ) -> None:
        if len(signing_key) < 32 or not issuer or not audience or audience == "*":
            raise ValueError("invalid_access_token_configuration")
        self.uow, self.revocations, self.key = uow, revocations, signing_key
        self.issuer, self.audience, self.lifetime = issuer, audience, lifetime_seconds

    def issue(self, tenant_id: str, session_id: str, membership_id: str) -> str:
        row = self.uow.connection.execute(
            "SELECT s.identity_id,s.status,s.authentication_strength,i.status identity_status,"
            "i.security_version,m.status membership_status FROM novaid_authentication_sessions s "
            "JOIN novaid_identities i ON i.identity_id=s.identity_id AND i.tenant_id=s.tenant_id "
            "JOIN novaid_tenant_memberships m ON m.identity_id=i.identity_id AND m.tenant_id=i.tenant_id "
            "WHERE s.session_id=? AND s.tenant_id=? AND m.membership_id=?",
            (session_id, tenant_id, membership_id),
        ).fetchone()
        if not row or (row["status"], row["identity_status"], row["membership_status"]) != (
            "ACTIVE",
            "ACTIVE",
            "ACTIVE",
        ):
            raise AccessTokenError("INVALID_ACCESS_TOKEN")
        now = datetime.now(UTC)
        payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": row["identity_id"],
            "jti": str(uuid4()),
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=self.lifetime)).timestamp()),
            "tenant_id": tenant_id,
            "session_id": session_id,
            "membership_id": membership_id,
            "authentication_strength": row["authentication_strength"],
            "security_version": row["security_version"],
            "token_version": 1,
        }
        header = {"alg": "HS256", "typ": "JWT"}
        signing = f"{_encode(json.dumps(header, separators=(',', ':')).encode())}.{_encode(json.dumps(payload, separators=(',', ':')).encode())}"
        signature = hmac.new(self.key, signing.encode(), hashlib.sha256).digest()
        return f"{signing}.{_encode(signature)}"

    def validate(
        self, token: str, *, expected_tenant: str, minimum_strength: str = "PASSWORD_OTP"
    ) -> dict[str, object]:
        try:
            encoded_header, encoded_payload, signature = token.split(".")
            header = json.loads(_decode(encoded_header))
            payload = json.loads(_decode(encoded_payload))
        except Exception as exc:
            raise AccessTokenError("INVALID_ACCESS_TOKEN") from exc
        signing = f"{encoded_header}.{encoded_payload}"
        expected = hmac.new(self.key, signing.encode(), hashlib.sha256).digest()
        if header.get("alg") != "HS256" or not hmac.compare_digest(expected, _decode(signature)):
            raise AccessTokenError("INVALID_ACCESS_TOKEN")
        now = int(datetime.now(UTC).timestamp())
        required = {
            "iss",
            "aud",
            "sub",
            "jti",
            "iat",
            "nbf",
            "exp",
            "tenant_id",
            "session_id",
            "membership_id",
            "authentication_strength",
            "security_version",
            "token_version",
        }
        if (
            not required.issubset(payload)
            or payload["iss"] != self.issuer
            or payload["aud"] != self.audience
        ):
            raise AccessTokenError("INVALID_ACCESS_TOKEN")
        if payload["exp"] <= now or payload["nbf"] > now:
            raise AccessTokenError("ACCESS_TOKEN_EXPIRED")
        if payload["tenant_id"] != expected_tenant:
            raise AccessTokenError("TENANT_ACCESS_DENIED")
        if self.revocations.is_session_revoked(expected_tenant, payload["session_id"]):
            raise AccessTokenError("SESSION_REVOKED")
        row = self.uow.connection.execute(
            "SELECT s.status,s.idle_expires_at,s.absolute_expires_at,s.expires_at,"
            "i.status identity_status,i.security_version,m.status membership_status "
            "FROM novaid_authentication_sessions s JOIN novaid_identities i ON i.identity_id=s.identity_id "
            "JOIN novaid_tenant_memberships m ON m.identity_id=i.identity_id AND m.tenant_id=i.tenant_id "
            "WHERE s.session_id=? AND s.tenant_id=? AND m.membership_id=?",
            (payload["session_id"], expected_tenant, payload["membership_id"]),
        ).fetchone()
        if not row or row["status"] != "ACTIVE":
            raise AccessTokenError("SESSION_REVOKED")
        instant = datetime.now(UTC)
        expiry_values = [row["idle_expires_at"], row["absolute_expires_at"] or row["expires_at"]]
        if any(value and datetime.fromisoformat(value) <= instant for value in expiry_values):
            self.uow.connection.execute(
                "UPDATE novaid_authentication_sessions SET status='EXPIRED',expired_at=?,"
                "revoked_at=?,revocation_reason='ON_ACCESS_EXPIRY' WHERE tenant_id=? "
                "AND session_id=? AND status='ACTIVE'",
                (instant.isoformat(), instant.isoformat(), expected_tenant, payload["session_id"]),
            )
            raise AccessTokenError("SESSION_EXPIRED")
        if row["identity_status"] != "ACTIVE" or row["membership_status"] != "ACTIVE":
            raise AccessTokenError("INVALID_ACCESS_TOKEN")
        if row["security_version"] != payload["security_version"]:
            raise AccessTokenError("INVALID_ACCESS_TOKEN")
        strengths = {
            "PASSWORD": 1,
            "OTP": 2,
            "PASSWORD_OTP": 3,
            "WEBAUTHN": 4,
            "PASSKEY": 5,
            "PHISHING_RESISTANT": 6,
        }
        if strengths.get(str(payload["authentication_strength"]), 0) < strengths.get(
            minimum_strength, 99
        ):
            raise AccessTokenError("STEP_UP_REQUIRED")
        return payload
