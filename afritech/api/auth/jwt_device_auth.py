from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, Security, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from afritech.afriprogramming.rbac import AUTH_ROLE_ORDER, canonical_role_name, role_implies_role
from afritech.security.device_identity import DeviceIdentity, DeviceRegistry


def _b64url_encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


def _b64url_decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)


@dataclass(frozen=True)
class JWTClaims:
    sub: str
    role: str
    organization_id: str
    tenant_id: str = ""
    workspace_id: str | None = None
    roles: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    region: str = "australia-southeast"
    exp: int = 0
    sid: str = ""
    token_kind: str = "access"


class InvalidTokenError(ValueError):
    pass


def _tuple_claim(payload: dict[str, object], name: str) -> tuple[str, ...]:
    value = payload.get(name, [])
    if not isinstance(value, list):
        raise InvalidTokenError(f"{name}_must_be_list")
    return tuple(str(item) for item in value)


class JWTService:
    """Minimal HS256 JWT service for controlled pilot authentication."""

    def __init__(self, secret: str, ttl_seconds: int = 12 * 60 * 60) -> None:
        if not secret:
            raise ValueError("secret must be non-empty")
        self.secret = secret.encode("utf-8")
        self.ttl_seconds = ttl_seconds

    def create_token(
        self,
        user_id: str,
        *,
        role: str = "OPERATOR",
        organization_id: str | None = None,
        tenant_id: str | None = None,
        workspace_id: str | None = None,
        roles: tuple[str, ...] | list[str] | None = None,
        permissions: tuple[str, ...] | list[str] | None = None,
        region: str | None = None,
        session_id: str | None = None,
        token_kind: str = "access",
        issued_at: int | None = None,
    ) -> str:
        now = int(time.time()) if issued_at is None else issued_at
        role = canonical_role_name(role)
        if role not in AUTH_ROLES:
            raise ValueError("invalid_role")
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user_id,
            "role": role,
            "exp": now + self.ttl_seconds,
            "token_kind": token_kind,
        }
        if organization_id:
            payload["organization_id"] = organization_id
        if tenant_id:
            payload["tenant_id"] = tenant_id
        if workspace_id:
            payload["workspace_id"] = workspace_id
        if roles:
            payload["roles"] = list(roles)
        if permissions:
            payload["permissions"] = list(permissions)
        if region:
            payload["region"] = region
        if session_id:
            payload["sid"] = session_id
        signing_input = ".".join(
            (
                _b64url_encode(json.dumps(header, sort_keys=True, separators=(",", ":")).encode()),
                _b64url_encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()),
            )
        )
        signature = hmac.new(self.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
        return f"{signing_input}.{_b64url_encode(signature)}"

    def verify_token(self, token: str, *, now: int | None = None) -> JWTClaims:
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
        except ValueError as exc:
            raise ValueError("invalid_token") from exc

        signing_input = f"{encoded_header}.{encoded_payload}"
        expected = hmac.new(self.secret, signing_input.encode("ascii"), hashlib.sha256).digest()
        supplied = _b64url_decode(encoded_signature)
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("invalid_signature")

        header = json.loads(_b64url_decode(encoded_header))
        if header.get("alg") != "HS256":
            raise ValueError("invalid_algorithm")

        try:
            payload = json.loads(_b64url_decode(encoded_payload))
        except json.JSONDecodeError as exc:
            raise InvalidTokenError("invalid_payload") from exc
        current_time = int(time.time()) if now is None else now
        if int(payload["exp"]) < current_time:
            raise InvalidTokenError("token_expired")
        role = canonical_role_name(str(payload.get("role", "OPERATOR")))
        if role not in AUTH_ROLES:
            raise InvalidTokenError("invalid_role")
        organization_id = str(
            payload.get("organization_id", payload.get("tenant_id", "afritech-core"))
        )
        tenant_id = str(payload.get("tenant_id", organization_id))
        return JWTClaims(
            sub=str(payload["sub"]),
            role=role,
            organization_id=organization_id,
            tenant_id=tenant_id,
            workspace_id=str(payload["workspace_id"]) if payload.get("workspace_id") is not None else None,
            roles=_tuple_claim(payload, "roles"),
            permissions=_tuple_claim(payload, "permissions"),
            region=str(payload.get("region", "australia-southeast")),
            exp=int(payload["exp"]),
            sid=str(payload["sid"]) if payload.get("sid") else "",
            token_kind=str(payload.get("token_kind", "access")),
        )


class DeviceBindingService:
    """Bind authenticated pilot users to registered device public keys."""

    def __init__(self, registry: DeviceRegistry | None = None) -> None:
        self.registry = registry or DeviceRegistry()

    def register_device(self, *, device_id: str, user_id: str, public_key: str, registered_at: int) -> DeviceIdentity:
        identity = DeviceIdentity(
            device_id=device_id,
            user_id=user_id,
            public_key=public_key,
            registered_at=registered_at,
        )
        self.registry.register(identity)
        return identity


AUTH_ROLES = frozenset(AUTH_ROLE_ORDER)
_EPHEMERAL_JWT_SECRET = secrets.token_urlsafe(48)
JWT = JWTService(os.environ.get("AFRITECH_JWT_SECRET", _EPHEMERAL_JWT_SECRET))
BEARER_SCHEME = HTTPBearer(auto_error=False, scheme_name="bearerAuth", bearerFormat="JWT")


def _cookie_secure() -> bool:
    environment = os.environ.get("AFRITECH_ENV", "development").lower()
    if environment in {"production", "prod"}:
        return True
    return os.environ.get("NOVACODEPRO_COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}


def build_auth_router(
    jwt_service: JWTService | None = None,
    device_binding: DeviceBindingService | None = None,
    session_store: Any | None = None,
) -> APIRouter:
    jwt = jwt_service or JWT
    binding = device_binding or DeviceBindingService()
    from afritech.api.auth.novacodepro_session_store import (
        ACCESS_COOKIE_NAME,
        CSRF_COOKIE_NAME,
        REFRESH_COOKIE_NAME,
        SESSION_COOKIE_NAME,
        get_default_novacodepro_session_store,
        set_default_novacodepro_session_store,
    )

    session_store = session_store or get_default_novacodepro_session_store()
    session_store.jwt_service = jwt
    set_default_novacodepro_session_store(session_store)
    router = APIRouter(prefix="/v1", tags=["pilot-auth"])

    @router.post("/auth/token")
    def create_token(
        payload: dict[str, Any],
        x_afritech_bootstrap_secret: str = Header(default=""),
    ) -> dict[str, str]:
        environment = os.environ.get("AFRITECH_ENV", "development").lower()
        if environment in {"production", "prod"}:
            enabled = os.environ.get(
                "AFRITECH_ALLOW_PILOT_TOKEN_ISSUANCE", ""
            ).lower() in {"1", "true", "yes"}
            expected = os.environ.get("AFRITECH_AUTH_BOOTSTRAP_SECRET", "")
            if (
                not enabled
                or not expected
                or not hmac.compare_digest(x_afritech_bootstrap_secret, expected)
            ):
                raise HTTPException(
                    status_code=403,
                    detail="production_token_issuance_disabled",
                )
        user_id = str(payload.get("user_id", ""))
        role = str(payload.get("role", "OPERATOR")).upper()
        organization_id = payload.get("organization_id", payload.get("tenant_id"))
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")
        if role not in AUTH_ROLES:
            raise HTTPException(status_code=400, detail="invalid_role")
        return {
            "token": jwt.create_token(
                user_id,
                role=role,
                organization_id=str(organization_id) if organization_id else None,
            )
        }

    @router.post("/devices/register")
    def register_device(payload: dict[str, Any], authorization: str = Header(default="")) -> dict[str, Any]:
        claims = _claims_from_authorization(jwt, authorization)
        user_id = str(payload.get("user_id", claims.sub))
        if user_id != claims.sub:
            raise HTTPException(status_code=403, detail="device user mismatch")

        try:
            identity = binding.register_device(
                device_id=str(payload["device_id"]),
                user_id=user_id,
                public_key=str(payload["public_key"]),
                registered_at=int(payload.get("registered_at", int(time.time()))),
            )
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return identity.canonical()

    @router.post("/auth/login")
    def login(payload: dict[str, Any], response: Response, request: Request) -> dict[str, Any]:
        identifier = str(
            payload.get("identifier") or payload.get("email") or payload.get("username") or ""
        ).strip()
        password = str(payload.get("password") or "")
        role = payload.get("role")
        if not identifier or not password:
            raise HTTPException(status_code=400, detail="email_and_password_required")
        result = session_store.login(
            identifier=identifier,
            password=password,
            role=str(role) if role else None,
            user_agent=request.headers.get("user-agent", ""),
            client_ip=request.client.host if request.client else "",
        )
        response.set_cookie(
            key=ACCESS_COOKIE_NAME,
            value=result["access_token"],
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            path="/",
        )
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=result["refresh_token"],
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            path="/",
        )
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=result["session_id"],
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            path="/",
        )
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=result["csrf_token"],
            httponly=False,
            secure=_cookie_secure(),
            samesite="lax",
            path="/",
        )
        return {
            "status": "authenticated",
            "user": {
                "user_id": result["session"]["user_id"],
                "email": result["session"]["email"],
                "display_name": result["session"]["display_name"],
                "organization": result["session"]["organization"],
                "assigned_roles": result["session"]["assigned_roles"],
                "active_role": result["session"]["active_role"],
            },
            "session": result["session"],
            "tokens": {
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"],
            },
        }

    @router.post("/session/login")
    def session_login(payload: dict[str, Any], response: Response, request: Request) -> dict[str, Any]:
        return login(payload, response, request)

    @router.get("/auth/session")
    def session(request: Request) -> dict[str, Any]:
        return session_store.current_session(request)

    @router.get("/session")
    def session_alias(request: Request) -> dict[str, Any]:
        return session_store.current_session(request)

    @router.get("/session/bootstrap")
    def session_bootstrap(request: Request) -> dict[str, Any]:
        return session_store.current_session(request)

    @router.post("/auth/session/keepalive")
    def keepalive(request: Request) -> dict[str, Any]:
        claims = session_store.claims_from_request(request)
        if claims is None or not claims.sid:
            raise HTTPException(status_code=401, detail="session_required")
        return {"status": "ok", "session": session_store.get_session(claims.sid)}

    @router.post("/auth/refresh")
    def refresh(request: Request, response: Response) -> dict[str, Any]:
        result = session_store.refresh_session(request)
        response.set_cookie(
            key=ACCESS_COOKIE_NAME,
            value=result["access_token"],
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            path="/",
        )
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=result["refresh_token"],
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            path="/",
        )
        return result

    @router.post("/session/refresh")
    def session_refresh(request: Request, response: Response) -> dict[str, Any]:
        return refresh(request, response)

    @router.post("/auth/logout")
    def logout(request: Request, response: Response) -> dict[str, Any]:
        result = session_store.logout(request)
        for cookie_name in (ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME, SESSION_COOKIE_NAME, CSRF_COOKIE_NAME):
            response.delete_cookie(cookie_name, path="/")
        response.headers["Cache-Control"] = "no-store"
        return result

    @router.post("/session/logout")
    def session_logout(request: Request, response: Response) -> dict[str, Any]:
        return logout(request, response)

    @router.post("/auth/switch-role")
    def switch_role(payload: dict[str, Any], request: Request, response: Response) -> dict[str, Any]:
        requested_role = str(payload.get("role") or "").strip()
        if not requested_role:
            raise HTTPException(status_code=400, detail="role required")
        result = session_store.switch_role(request, requested_role)
        response.set_cookie(
            key=ACCESS_COOKIE_NAME,
            value=result["access_token"],
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            path="/",
        )
        return result

    @router.get("/auth/me")
    def me(request: Request) -> dict[str, Any]:
        return session_store.current_session(request)

    return router


def build_novacodepro_session_router(
    jwt_service: JWTService | None = None,
    device_binding: DeviceBindingService | None = None,
    session_store: Any | None = None,
) -> APIRouter:
    jwt = jwt_service or JWT
    _ = device_binding or DeviceBindingService()
    from afritech.api.auth.novacodepro_session_store import (
        ACCESS_COOKIE_NAME,
        CSRF_COOKIE_NAME,
        REFRESH_COOKIE_NAME,
        SESSION_COOKIE_NAME,
        get_default_novacodepro_session_store,
        set_default_novacodepro_session_store,
    )

    session_store = session_store or get_default_novacodepro_session_store()
    session_store.jwt_service = jwt
    set_default_novacodepro_session_store(session_store)
    router = APIRouter(prefix="/v1/novacodepro", tags=["novacodepro-session"])

    def _set_session_cookies(response: Response, result: dict[str, Any]) -> None:
        response.set_cookie(
            key=ACCESS_COOKIE_NAME,
            value=result["access_token"],
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            path="/",
        )
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=result["refresh_token"],
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            path="/",
        )
        session_id = result.get("session_id") or result.get("session", {}).get("session_id")
        if session_id:
            response.set_cookie(
                key=SESSION_COOKIE_NAME,
                value=str(session_id),
                httponly=True,
                secure=_cookie_secure(),
                samesite="lax",
                path="/",
            )
        csrf_token = result.get("csrf_token")
        if csrf_token:
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=str(csrf_token),
                httponly=False,
                secure=_cookie_secure(),
                samesite="lax",
                path="/",
            )

    def _clear_session_cookies(response: Response) -> None:
        for cookie_name in (ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME, SESSION_COOKIE_NAME, CSRF_COOKIE_NAME):
            response.delete_cookie(cookie_name, path="/")

    @router.post("/session/login")
    def session_login(payload: dict[str, Any], response: Response, request: Request) -> dict[str, Any]:
        identifier = str(
            payload.get("identifier") or payload.get("email") or payload.get("username") or ""
        ).strip()
        password = str(payload.get("password") or "")
        role = payload.get("role")
        if not identifier or not password:
            raise HTTPException(status_code=400, detail="email_and_password_required")
        result = session_store.login(
            identifier=identifier,
            password=password,
            role=str(role) if role else None,
            user_agent=request.headers.get("user-agent", ""),
            client_ip=request.client.host if request.client else "",
        )
        _set_session_cookies(response, result)
        return {
            "status": "authenticated",
            "user": {
                "user_id": result["session"]["user_id"],
                "email": result["session"]["email"],
                "display_name": result["session"]["display_name"],
                "organization": result["session"]["organization"],
                "assigned_roles": result["session"]["assigned_roles"],
                "active_role": result["session"]["active_role"],
            },
            "session": result["session"],
            "tokens": {
                "access_token": result["access_token"],
                "refresh_token": result["refresh_token"],
            },
        }

    @router.get("/session")
    def session(request: Request) -> dict[str, Any]:
        return session_store.current_session(request)

    @router.get("/session/bootstrap")
    def session_bootstrap(request: Request) -> dict[str, Any]:
        return session_store.current_session(request)

    @router.post("/session/refresh")
    def session_refresh(request: Request, response: Response) -> dict[str, Any]:
        result = session_store.refresh_session(request)
        _set_session_cookies(response, result)
        return result

    @router.post("/session/logout")
    def session_logout(request: Request, response: Response) -> dict[str, Any]:
        result = session_store.logout(request)
        _clear_session_cookies(response)
        response.headers["Cache-Control"] = "no-store"
        return result

    return router


def _claims_from_credentials(
    jwt: JWTService,
    credentials: HTTPAuthorizationCredentials | None,
) -> JWTClaims:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="bearer token required")
    try:
        return jwt.verify_token(credentials.credentials)
    except (InvalidTokenError, ValueError) as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def _claims_from_authorization(jwt: JWTService, authorization: str) -> JWTClaims:
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="bearer token required")
    return _claims_from_credentials(
        jwt,
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=authorization[len(prefix) :]),
    )


def get_current_claims(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(BEARER_SCHEME),
) -> JWTClaims:
    if credentials and credentials.credentials:
        claims = _claims_from_credentials(JWT, credentials)
    else:
        claims = None
    if claims is not None and claims.sid:
        from afritech.api.auth.novacodepro_session_store import get_default_novacodepro_session_store

        session_store = get_default_novacodepro_session_store()
        session_store._validate_access_token_session(claims.sid, credentials.credentials)  # noqa: SLF001
        return session_store.get_claims_for_session(claims.sid)
    if claims is not None:
        return claims

    from afritech.api.auth.novacodepro_session_store import get_default_novacodepro_session_store

    session_store = get_default_novacodepro_session_store()
    session_claims = session_store.claims_from_request(request)
    if session_claims is None:
        raise HTTPException(status_code=401, detail="bearer token required")
    return session_claims


def require_roles(*roles: str):
    allowed = {getattr(role, "value", role).upper() for role in roles}

    def dependency(claims: JWTClaims = Depends(get_current_claims)) -> JWTClaims:
        if allowed and not any(role_implies_role(claims.role, required) for required in allowed):
            raise HTTPException(status_code=403, detail="insufficient_role")
        return claims

    return dependency


def authenticate_websocket(
    websocket: WebSocket,
    *,
    roles: set[str] | None = None,
) -> JWTClaims | None:
    token = websocket.query_params.get("token")
    if token is None:
        authorization = websocket.headers.get("authorization", "")
        if authorization.startswith("Bearer "):
            token = authorization[len("Bearer ") :]
    if not token:
        return None
    try:
        claims = JWT.verify_token(token)
    except ValueError:
        return None
    if roles and claims.role not in roles:
        return None
    return claims


async def reject_websocket(websocket: WebSocket) -> None:
    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
