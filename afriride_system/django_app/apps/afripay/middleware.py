"""Security middleware for AfriPay routes."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
import os
import time
from typing import Callable

from django.http import JsonResponse

from afritech.afriprogramming.rbac import canonical_role_name, role_payment_scopes
from afriride_system.api.auth import JWTService
from afriride_system.django_app.apps.afripay.security import (
    AfriPayRateLimiter,
    APIKeyService,
    OAuth2TokenService,
    parse_authorization_header,
    SecurityPrincipal,
    send_auth_alert,
)


@dataclass(frozen=True)
class RequiredScope:
    path_prefix: str
    scope: str


class AfriPaySecurityMiddleware:
    EXEMPT_PATHS = {
        "/api/afripay/auth/oauth/token",
        "/api/novapay/auth/oauth/token",
        "/api/afripay/metrics/prometheus",
        "/api/novapay/metrics/prometheus",
    }
    EXEMPT_PREFIXES = (
        "/api/afripay/webhooks/",
        "/api/novapay/webhooks/",
    )

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.rate_limiter = AfriPayRateLimiter()
        self.oauth = OAuth2TokenService()
        self.api_keys = APIKeyService()

    def __call__(self, request):
        path = getattr(request, "path", "")
        if not path.startswith(("/api/afripay", "/api/novapay")):
            return self.get_response(request)

        identity_key = request.META.get("REMOTE_ADDR", "anonymous")
        if not self.rate_limiter.allow(identity_key):
            send_auth_alert("AFRIPAY_RATE_LIMIT_EXCEEDED", {"identity": identity_key, "path": path})
            return JsonResponse({"detail": "rate limit exceeded"}, status=429)

        if path in self.EXEMPT_PATHS or any(
            path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES
        ):
            return self.get_response(request)

        auth = parse_authorization_header(request.headers.get("Authorization", ""))
        if auth is None:
            api_key = request.headers.get("X-API-Key", "").strip()
            if api_key:
                auth = ("api_key", api_key)

        if auth is None:
            send_auth_alert("AFRIPAY_AUTH_MISSING", {"path": path})
            return JsonResponse({"detail": "authentication required"}, status=401)

        scheme, token = auth
        try:
            if scheme == "oauth2":
                try:
                    principal = self.oauth.verify_access_token(token)
                except ValueError as exc:
                    principal = self._principal_from_role_token(token, exc)
            else:
                principal = self.api_keys.authenticate(token)
        except ValueError as exc:
            send_auth_alert(
                "AFRIPAY_AUTH_FAILURE",
                {"path": path, "reason": str(exc), "scheme": scheme},
            )
            status = (
                401
                if "invalid" in str(exc) or "expired" in str(exc) or "suspended" in str(exc)
                else 403
            )
            return JsonResponse({"detail": str(exc)}, status=status)

        request.afripay_principal = principal
        request.afripay_auth_scheme = principal.scheme
        request.afripay_scopes = set(principal.scopes)
        request.afripay_identity = principal.subject
        return self.get_response(request)

    @staticmethod
    def _principal_from_role_token(token: str, original_error: ValueError):
        secret = os.environ.get("AFRIRIDE_JWT_SECRET", "")
        try:
            claims = JWTService(secret).verify_token(token)
        except ValueError as exc:
            if str(exc) != "missing_required_claim":
                raise original_error from exc
            claims = AfriPaySecurityMiddleware._legacy_role_token_claims(token, secret)
        scopes = role_payment_scopes(claims.role)
        if not scopes:
            raise original_error
        return SecurityPrincipal(
            subject=claims.sub,
            scheme="rbac_jwt",
            scopes=tuple(scopes),
            client_name=claims.role,
        )

    @staticmethod
    def _legacy_role_token_claims(token: str, secret: str):
        if not secret:
            raise ValueError("missing_required_claim")
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
            header = json.loads(_b64url_decode(encoded_header))
            payload = json.loads(_b64url_decode(encoded_payload))
        except Exception as exc:  # pragma: no cover - defensive parse guard
            raise ValueError("invalid_token") from exc
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise ValueError("invalid_algorithm")
        signing_input = f"{encoded_header}.{encoded_payload}"
        expected = hmac.new(secret.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        supplied = _b64url_decode(encoded_signature)
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("invalid_signature")
        if int(payload.get("exp", 0)) <= int(time.time()):
            raise ValueError("token_expired")
        role = canonical_role_name(str(payload.get("role", "")))
        if not role:
            raise ValueError("invalid_role")

        class LegacyClaims:
            def __init__(self, sub: str, role: str) -> None:
                self.sub = sub
                self.role = role

        return LegacyClaims(sub=str(payload.get("sub", "")), role=role)


def _b64url_decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)
