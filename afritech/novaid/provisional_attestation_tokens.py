"""Cryptographically distinct, attestation-only bootstrap credentials."""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from .tokens import _decode, _encode


class ProvisionalAttestationTokenError(ValueError):
    pass


class ProvisionalAttestationTokenService:
    TOKEN_USE = "DEVICE_ATTESTATION_BOOTSTRAP"
    AUDIENCE = "novaid-device-attestation"

    def __init__(self, uow_provider, *, signing_keys: dict[str, bytes], active_key_id: str,
                 issuer: str, lifetime_seconds: int = 180) -> None:
        if lifetime_seconds <= 0 or lifetime_seconds > 600:
            raise ValueError("invalid_provisional_token_lifetime")
        self.uow_provider = uow_provider
        self.signing_keys, self.active_key_id = signing_keys, active_key_id
        self.issuer, self.lifetime_seconds = issuer, lifetime_seconds

    def issue(self, *, tenant_id: str, subject_id: str, session_id: str,
              membership_id: str, device_id: str, security_version: int) -> str:
        now = int(datetime.now(UTC).timestamp())
        payload = {
            "iss": self.issuer, "aud": self.AUDIENCE, "sub": subject_id,
            "tenant_id": tenant_id, "session_id": session_id,
            "membership_id": membership_id, "device_id": device_id,
            "security_version": security_version, "token_use": self.TOKEN_USE,
            "scope": ["device_attestation:challenge", "device_attestation:verify"],
            "jti": str(uuid4()), "iat": now, "nbf": now, "exp": now + self.lifetime_seconds,
        }
        header = {"alg": "HS256", "typ": "NOVAID-ATTESTATION+JWT", "kid": self.active_key_id}
        signing = f"{_encode(json.dumps(header, separators=(',', ':')).encode())}.{_encode(json.dumps(payload, separators=(',', ':')).encode())}"
        signature = hmac.new(self.signing_keys[self.active_key_id], signing.encode(), hashlib.sha256).digest()
        return f"{signing}.{_encode(signature)}"

    def validate(self, token: str, *, expected_tenant: str) -> dict[str, Any]:
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
            header, payload = json.loads(_decode(encoded_header)), json.loads(_decode(encoded_payload))
            signature = _decode(encoded_signature)
        except Exception as exc:
            raise ProvisionalAttestationTokenError("INVALID_PROVISIONAL_TOKEN") from exc
        key = self.signing_keys.get(header.get("kid"))
        expected = hmac.new(key or b"invalid", f"{encoded_header}.{encoded_payload}".encode(), hashlib.sha256).digest()
        now = int(datetime.now(UTC).timestamp())
        if (key is None or header != {"alg": "HS256", "typ": "NOVAID-ATTESTATION+JWT", "kid": header.get("kid")}
                or not hmac.compare_digest(signature, expected)
                or payload.get("iss") != self.issuer or payload.get("aud") != self.AUDIENCE
                or payload.get("token_use") != self.TOKEN_USE
                or payload.get("scope") != ["device_attestation:challenge", "device_attestation:verify"]
                or payload.get("tenant_id") != expected_tenant
                or not isinstance(payload.get("exp"), int) or payload["exp"] <= now):
            raise ProvisionalAttestationTokenError("INVALID_PROVISIONAL_TOKEN")
        with self.uow_provider() as uow:
            row = uow.device_attestation_sessions.provisional_context(
                expected_tenant, str(payload.get("session_id", ""))
            )
        if (row is None or row["status"] != "PENDING_DEVICE_ATTESTATION"
                or str(row["identity_id"]) != payload.get("sub")
                or str(row["membership_id"]) != payload.get("membership_id")
                or str(row["device_reference"]) != payload.get("device_id")
                or int(row["identity_security_version"]) != payload.get("security_version")):
            raise ProvisionalAttestationTokenError("PROVISIONAL_CONTEXT_INVALID")
        return payload
