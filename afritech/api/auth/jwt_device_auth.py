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

from fastapi import APIRouter, Depends, Header, HTTPException, Security, WebSocket, status
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
    exp: int


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
        }
        if organization_id:
            payload["organization_id"] = organization_id
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

        payload = json.loads(_b64url_decode(encoded_payload))
        current_time = int(time.time()) if now is None else now
        if int(payload["exp"]) < current_time:
            raise ValueError("token_expired")
        role = canonical_role_name(str(payload.get("role", "OPERATOR")))
        if role not in AUTH_ROLES:
            raise ValueError("invalid_role")
        organization_id = str(
            payload.get("organization_id", payload.get("tenant_id", "afritech-core"))
        )
        return JWTClaims(
            sub=str(payload["sub"]),
            role=role,
            organization_id=organization_id,
            exp=int(payload["exp"]),
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


def build_auth_router(
    jwt_service: JWTService | None = None,
    device_binding: DeviceBindingService | None = None,
) -> APIRouter:
    jwt = jwt_service or JWT
    binding = device_binding or DeviceBindingService()
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

    return router


def _claims_from_credentials(
    jwt: JWTService,
    credentials: HTTPAuthorizationCredentials | None,
) -> JWTClaims:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="bearer token required")
    try:
        return jwt.verify_token(credentials.credentials)
    except ValueError as exc:
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
    credentials: HTTPAuthorizationCredentials | None = Security(BEARER_SCHEME),
) -> JWTClaims:
    return _claims_from_credentials(JWT, credentials)


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
