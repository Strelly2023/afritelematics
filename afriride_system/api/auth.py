"""Fail-closed authentication and authorization for the NovaRide API."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from afritech.afriprogramming.rbac import AUTH_ROLE_ORDER, canonical_role_name, role_implies_role


ROLES = frozenset(AUTH_ROLE_ORDER)
DEFAULT_ISSUER = "novaride-api"
DEFAULT_AUDIENCE = "novaride-clients"


def _b64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _b64url_decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)


@dataclass(frozen=True)
class AuthClaims:
    sub: str
    role: str
    exp: int
    iss: str = DEFAULT_ISSUER
    aud: str = DEFAULT_AUDIENCE
    iat: int = 0
    nbf: int = 0
    jti: str = "legacy-internal-claim"
    session_id: str = "legacy-internal-session"
    tenant_id: str | None = None
    roles: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    region: str = "australia-southeast"

    @property
    def organization_id(self) -> str:
        return self.tenant_id or "afritech-core"


@dataclass(frozen=True)
class IdentityRecord:
    user_id: str
    password_hash: str
    role: str
    tenant_id: str | None
    status: str = "ACTIVE"
    membership_status: str = "ACTIVE"


class IdentityStore:
    """Authoritative, server-controlled identity records used by NovaRide."""

    def __init__(self, records: Mapping[str, IdentityRecord] | None = None) -> None:
        self._records = dict(records or {})

    @classmethod
    def from_environment(cls) -> "IdentityStore":
        raw = os.environ.get("AFRIRIDE_IDENTITY_RECORDS_JSON", "")
        if not raw:
            return cls()
        try:
            payload = json.loads(raw)
            records = {
                str(identifier): IdentityRecord(
                    user_id=str(value["user_id"]),
                    password_hash=str(value["password_hash"]),
                    role=canonical_role_name(str(value["role"])),
                    tenant_id=str(value["tenant_id"]) if value.get("tenant_id") else None,
                    status=str(value.get("status", "ACTIVE")).upper(),
                    membership_status=str(value.get("membership_status", "ACTIVE")).upper(),
                )
                for identifier, value in payload.items()
            }
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise RuntimeError("invalid_identity_store_configuration") from exc
        return cls(records)

    def authenticate(self, identifier: str, password: str) -> IdentityRecord:
        record = self._records.get(identifier)
        supplied = _password_digest(password, record.password_hash if record else _dummy_password_hash())
        expected = record.password_hash if record else _dummy_password_hash()
        if record is None or not hmac.compare_digest(supplied, expected):
            raise ValueError("invalid_credentials")
        if record.status != "ACTIVE":
            raise ValueError("account_disabled")
        if record.membership_status != "ACTIVE":
            raise ValueError("tenant_membership_invalid")
        if record.role not in ROLES:
            raise ValueError("identity_role_invalid")
        return record


def password_hash(password: str, *, salt: str | None = None) -> str:
    selected_salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), selected_salt.encode(), 310_000)
    return f"pbkdf2_sha256$310000${selected_salt}${digest.hex()}"


def _password_digest(password: str, encoded: str) -> str:
    try:
        algorithm, iterations, salt, _ = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256" or int(iterations) < 310_000:
            return ""
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations))
        return f"{algorithm}${iterations}${salt}${digest.hex()}"
    except (TypeError, ValueError):
        return ""


def _dummy_password_hash() -> str:
    return "pbkdf2_sha256$310000$00000000000000000000000000000000$" + "0" * 64


class SessionRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._sessions: dict[str, dict[str, Any]] = {}

    def create(self, identity: IdentityRecord, *, expires_at: int) -> str:
        session_id = secrets.token_urlsafe(24)
        with self._lock:
            self._sessions[session_id] = {
                "user_id": identity.user_id,
                "tenant_id": identity.tenant_id,
                "expires_at": expires_at,
                "active": True,
            }
        return session_id

    def validate(self, session_id: str, subject: str, tenant_id: str | None, *, now: int) -> None:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise ValueError("unknown_session")
        if not session["active"]:
            raise ValueError("session_revoked")
        if int(session["expires_at"]) < now:
            raise ValueError("session_expired")
        if session["user_id"] != subject or session["tenant_id"] != tenant_id:
            raise ValueError("session_claim_mismatch")

    def revoke(self, session_id: str) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            session["active"] = False
            return True


class JWTService:
    def __init__(
        self,
        secret: str,
        ttl_seconds: int = 15 * 60,
        *,
        issuer: str = DEFAULT_ISSUER,
        audience: str = DEFAULT_AUDIENCE,
        sessions: SessionRegistry | None = None,
    ) -> None:
        if not secret:
            raise ValueError("secret must be non-empty")
        if not issuer or not audience:
            raise ValueError("issuer_and_audience_required")
        self.secret = secret.encode("utf-8")
        self.ttl_seconds = ttl_seconds
        self.issuer = issuer
        self.audience = audience
        self.sessions = sessions or SessionRegistry()

    def create_token(
        self,
        user_id: str,
        role: str,
        *,
        tenant_id: str | None = None,
        session_id: str | None = None,
        issued_at: int | None = None,
    ) -> str:
        """Create a token for trusted server-side callers and tests, never request payloads."""
        role = canonical_role_name(role)
        if role not in ROLES:
            raise ValueError("invalid_role")
        now = int(time.time()) if issued_at is None else issued_at
        expires_at = now + self.ttl_seconds
        if session_id is None:
            session_id = self.sessions.create(
                IdentityRecord(user_id, "", role, tenant_id), expires_at=expires_at
            )
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user_id,
            "role": role,
            "tenant_id": tenant_id,
            "iss": self.issuer,
            "aud": self.audience,
            "iat": now,
            "nbf": now,
            "exp": expires_at,
            "jti": secrets.token_urlsafe(18),
            "sid": session_id,
        }
        signing_input = ".".join(
            (
                _b64url_encode(json.dumps(header, sort_keys=True, separators=(",", ":")).encode()),
                _b64url_encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()),
            )
        )
        signature = hmac.new(self.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
        return f"{signing_input}.{_b64url_encode(signature)}"

    def verify_token(self, token: str, *, now: int | None = None) -> AuthClaims:
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
            supplied = _b64url_decode(encoded_signature)
            header = json.loads(_b64url_decode(encoded_header))
            payload = json.loads(_b64url_decode(encoded_payload))
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            raise ValueError("invalid_token") from exc
        signing_input = f"{encoded_header}.{encoded_payload}"
        expected = hmac.new(self.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("invalid_signature")
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise ValueError("invalid_algorithm")
        current_time = int(time.time()) if now is None else now
        required = {"sub", "role", "iss", "aud", "iat", "nbf", "exp", "jti", "sid"}
        if not required.issubset(payload):
            raise ValueError("missing_required_claim")
        if payload["iss"] != self.issuer:
            raise ValueError("invalid_issuer")
        if payload["aud"] != self.audience:
            raise ValueError("invalid_audience")
        if int(payload["iat"]) > current_time + 30 or int(payload["nbf"]) > current_time + 30:
            raise ValueError("token_not_yet_valid")
        if int(payload["exp"]) <= current_time:
            raise ValueError("token_expired")
        role = canonical_role_name(str(payload["role"]))
        if role not in ROLES:
            raise ValueError("invalid_role")
        claims = AuthClaims(
            sub=str(payload["sub"]), role=role, exp=int(payload["exp"]),
            iss=str(payload["iss"]), aud=str(payload["aud"]), iat=int(payload["iat"]),
            nbf=int(payload["nbf"]), jti=str(payload["jti"]), session_id=str(payload["sid"]),
            tenant_id=str(payload["tenant_id"]) if payload.get("tenant_id") else None,
        )
        self.sessions.validate(claims.session_id, claims.sub, claims.tenant_id, now=current_time)
        return claims


JWT = JWTService(
    os.environ.get("AFRIRIDE_JWT_SECRET", secrets.token_urlsafe(48)),
    issuer=os.environ.get("AFRIRIDE_JWT_ISSUER", DEFAULT_ISSUER),
    audience=os.environ.get("AFRIRIDE_JWT_AUDIENCE", DEFAULT_AUDIENCE),
)
IDENTITIES = IdentityStore.from_environment()


def build_auth_router(
    jwt_service: JWTService = JWT, identity_store: IdentityStore = IDENTITIES
) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/token")
    def create_token(payload: dict[str, Any]) -> dict[str, str]:
        if any(key in payload for key in ("user_id", "role", "permissions", "tenant_id", "is_admin")):
            raise HTTPException(status_code=403, detail="caller_controlled_claims_forbidden")
        identifier = str(payload.get("identifier", "")).strip()
        password = str(payload.get("password", ""))
        if not identifier or not password:
            raise HTTPException(status_code=401, detail="invalid_credentials")
        try:
            identity = identity_store.authenticate(identifier, password)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        token = jwt_service.create_token(
            identity.user_id, identity.role, tenant_id=identity.tenant_id
        )
        return {"token": token, "token_type": "bearer", "expires_in": str(jwt_service.ttl_seconds)}

    return router


PUBLIC_ROUTES = frozenset({("GET", "/"), ("GET", "/health"), ("POST", "/auth/token"), ("POST", "/v1/auth/token")})


def authorization_policy(method: str, path: str) -> dict[str, Any]:
    public = method == "OPTIONS" or (method, path) in PUBLIC_ROUTES
    roles = set() if public else _required_roles(method, path)
    return {
        "public": public,
        "authentication_required": not public,
        "allowed_roles": sorted(roles),
        "required_permission": None,
        "tenant_scope": "token_tenant" if not public else "none",
        "resource_ownership_rule": "route_handler_or_role_policy" if not public else "none",
    }


async def auth_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    policy = authorization_policy(request.method, request.url.path)
    if policy["public"]:
        return await call_next(request)
    required_roles = set(policy["allowed_roles"])
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        return _auth_error(401, "bearer token required")
    try:
        claims = JWT.verify_token(authorization[len("Bearer ") :])
    except ValueError as exc:
        return _auth_error(401, str(exc))
    if required_roles and not any(role_implies_role(claims.role, required) for required in required_roles):
        return _auth_error(403, "insufficient_role")
    request.state.auth_claims = claims
    return await call_next(request)


def _required_roles(method: str, path: str) -> set[str]:
    if path.startswith("/system/") or path == "/rides/active":
        return {"OPERATOR", "ADMIN"}
    if path == "/v1/operations/safety/distress":
        return {"CUSTOMER", "DRIVER", "DISPATCHER", "OPERATOR", "ADMIN"}
    if path.startswith("/v1/operations/"):
        return {"DISPATCHER", "FLEET_OWNER", "OPERATOR", "ADMIN"}
    if path.startswith("/v1/payments/"):
        return {"OPERATOR", "ADMIN"} if path.endswith(("/health", "/reporting")) else set(ROLES)
    if path.startswith("/v1/public-pilot/"):
        return set(ROLES)
    if path.startswith("/passenger/"):
        return {"CUSTOMER", "DRIVER", "DISPATCHER", "FLEET_OWNER", "ADMIN"} if method == "GET" else {"CUSTOMER", "ADMIN"}
    if path.startswith("/driver/"):
        return {"DRIVER", "DISPATCHER", "FLEET_OWNER", "ADMIN"}
    if path.startswith("/ride/"):
        return {"DRIVER", "ADMIN"} if method == "POST" else {"CUSTOMER", "DRIVER", "DISPATCHER", "FLEET_OWNER", "ADMIN"}
    return set(ROLES)


def _auth_error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"code": message.upper(), "message": message}})


def claims_from_request(request: Request | None) -> AuthClaims | None:
    return None if request is None else getattr(request.state, "auth_claims", None)


def get_current_claims(authorization: str = Header(default="")) -> AuthClaims:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="bearer token required")
    try:
        return JWT.verify_token(authorization[len("Bearer ") :])
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def require_roles(*required_roles: str):
    expected = {canonical_role_name(role) for role in required_roles}

    def dependency(claims: AuthClaims = Depends(get_current_claims)) -> AuthClaims:
        if not any(role_implies_role(claims.role, required) for required in expected):
            raise HTTPException(status_code=403, detail="insufficient_role")
        return claims

    return dependency
