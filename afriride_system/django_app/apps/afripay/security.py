"""Security primitives for AfriPay Django API."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Mapping

from django.utils import timezone

from afritech.monitoring.alerts import send_integrity_alert
from afriride_system.django_app.apps.afripay.models import APIKeyCredential, OAuthClient


def _b64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _b64url_decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)


@dataclass(frozen=True)
class SecurityPrincipal:
    subject: str
    scheme: str
    scopes: tuple[str, ...]
    client_name: str


class OAuth2TokenService:
    def __init__(self, secret: str | None = None, ttl_seconds: int = 600) -> None:
        self.secret = (
            secret
            or os.environ.get("AFRIPAY_OAUTH_SECRET")
            or "afripay-local-oauth-secret"
        ).encode("utf-8")
        self.ttl_seconds = ttl_seconds

    def issue_access_token(self, client: OAuthClient, scopes: list[str]) -> dict[str, Any]:
        now = int(time.time())
        payload = {
            "aud": "afripay",
            "client_id": client.client_id,
            "exp": now + self.ttl_seconds,
            "iat": now,
            "jti": secrets.token_hex(16),
            "scope": " ".join(sorted(scopes)),
            "sub": client.client_id,
            "token_type": "Bearer",
        }
        signing_input = ".".join(
            (
                _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}, sort_keys=True, separators=(",", ":")).encode("utf-8")),
                _b64url_encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")),
            )
        )
        signature = hmac.new(self.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
        token = f"{signing_input}.{_b64url_encode(signature)}"
        return {
            "access_token": token,
            "expires_in": self.ttl_seconds,
            "scope": payload["scope"],
            "token_type": "Bearer",
        }

    def verify_access_token(self, token: str) -> SecurityPrincipal:
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
        except ValueError as exc:
            raise ValueError("invalid_token") from exc

        signing_input = f"{encoded_header}.{encoded_payload}"
        expected = hmac.new(self.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
        supplied = _b64url_decode(encoded_signature)
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("invalid_signature")

        payload = json.loads(_b64url_decode(encoded_payload))
        if payload.get("aud") != "afripay":
            raise ValueError("invalid_audience")
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("token_expired")
        return SecurityPrincipal(
            subject=str(payload["sub"]),
            scheme="oauth2",
            scopes=tuple(str(payload.get("scope", "")).split()),
            client_name=str(payload.get("client_id", payload["sub"])),
        )


class APIKeyService:
    def issue_key(self, name: str, scopes: list[str]) -> tuple[APIKeyCredential, str]:
        raw_key = "afp_" + secrets.token_urlsafe(32)
        key_hash = APIKeyCredential.hash_key(raw_key)
        prefix = raw_key[:8]
        credential = APIKeyCredential.objects.create(
            key_id="key." + secrets.token_hex(12),
            name=name,
            key_hash=key_hash,
            prefix=prefix,
            scopes=scopes,
        )
        return credential, raw_key

    def authenticate(self, raw_key: str) -> SecurityPrincipal:
        key_hash = APIKeyCredential.hash_key(raw_key)
        credential = APIKeyCredential.objects.filter(key_hash=key_hash).first()
        if credential is None:
            raise ValueError("invalid_api_key")
        if not credential.is_active:
            raise ValueError("api_key_revoked")
        if credential.suspended_until and credential.suspended_until > timezone.now():
            raise ValueError("api_key_suspended")
        credential.last_used_at = timezone.now()
        credential.request_count += 1
        credential.save(update_fields=["last_used_at", "request_count", "updated_at"])
        return SecurityPrincipal(
            subject=credential.key_id,
            scheme="api_key",
            scopes=tuple(credential.scopes),
            client_name=credential.name,
        )


class AfriPayRateLimiter:
    def __init__(self, window_seconds: int = 60, max_requests: int = 120) -> None:
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self._requests: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time.time()
        window = [stamp for stamp in self._requests[key] if now - stamp < self.window_seconds]
        self._requests[key] = window
        if len(window) >= self.max_requests:
            return False
        self._requests[key].append(now)
        return True

    def snapshot(self) -> dict[str, Any]:
        now = time.time()
        return {
            key: len([stamp for stamp in stamps if now - stamp < self.window_seconds])
            for key, stamps in self._requests.items()
        }


def parse_authorization_header(header: str) -> tuple[str, str] | None:
    if not header:
        return None
    prefix, _, value = header.partition(" ")
    if not value:
        return None
    scheme = prefix.strip().lower()
    token = value.strip()
    if scheme == "bearer":
        return ("oauth2", token)
    if scheme in {"api-key", "apikey"}:
        return ("api_key", token)
    return None


def verify_oauth_client_credentials(client_id: str, client_secret: str, scope: str | None = None) -> OAuthClient:
    client = OAuthClient.objects.filter(client_id=client_id).first()
    if client is None:
        raise ValueError("invalid_client")
    if not client.is_active:
        raise ValueError("client_inactive")
    if client.suspended_until and client.suspended_until > timezone.now():
        raise ValueError("client_suspended")
    if client.expires_at and client.expires_at < timezone.now():
        raise ValueError("client_expired")
    if OAuthClient.hash_secret(client_secret) != client.secret_hash:
        client.failure_count += 1
        client.save(update_fields=["failure_count", "updated_at"])
        raise ValueError("invalid_client_secret")
    requested = [item for item in (scope or "").split() if item]
    if requested:
        allowed = set(client.scopes)
        if not set(requested).issubset(allowed):
            raise ValueError("invalid_scope")
    client.last_used_at = timezone.now()
    client.request_count += 1
    client.save(update_fields=["last_used_at", "request_count", "updated_at"])
    return client


def send_auth_alert(event_type: str, details: Mapping[str, Any]) -> None:
    send_integrity_alert(event_type, "HIGH", dict(details))
