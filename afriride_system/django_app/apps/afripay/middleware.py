"""Security middleware for AfriPay routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from django.http import JsonResponse

from afritech.monitoring.alerts import send_integrity_alert
from afriride_system.django_app.apps.afripay.security import (
    AfriPayRateLimiter,
    APIKeyService,
    OAuth2TokenService,
    parse_authorization_header,
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

        if path in self.EXEMPT_PATHS or any(path.startswith(prefix) for prefix in self.EXEMPT_PREFIXES):
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
                principal = self.oauth.verify_access_token(token)
            else:
                principal = self.api_keys.authenticate(token)
        except ValueError as exc:
            send_auth_alert("AFRIPAY_AUTH_FAILURE", {"path": path, "reason": str(exc), "scheme": scheme})
            status = 401 if "invalid" in str(exc) or "expired" in str(exc) or "suspended" in str(exc) else 403
            return JsonResponse({"detail": str(exc)}, status=status)

        request.afripay_principal = principal
        request.afripay_auth_scheme = scheme
        request.afripay_scopes = set(principal.scopes)
        request.afripay_identity = principal.subject
        return self.get_response(request)
