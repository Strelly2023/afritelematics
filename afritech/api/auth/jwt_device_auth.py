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

from fastapi import APIRouter, Depends, Header, HTTPException, WebSocket, status

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
        issued_at: int | None = None,
    ) -> str:
        now = int(time.time()) if issued_at is None else issued_at
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"sub": user_id, "role": role.upper(), "exp": now + self.ttl_seconds}
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
        role = str(payload.get("role", "OPERATOR")).upper()
        if role not in AUTH_ROLES:
            raise ValueError("invalid_role")
        return JWTClaims(sub=str(payload["sub"]), role=role, exp=int(payload["exp"]))


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


AUTH_ROLES = frozenset({"OPERATOR", "VERIFIER", "PARTNER", "DEVELOPER", "DEVICE", "OBSERVER"})
_EPHEMERAL_JWT_SECRET = secrets.token_urlsafe(48)
JWT = JWTService(os.environ.get("AFRITECH_JWT_SECRET", _EPHEMERAL_JWT_SECRET))


def build_auth_router(
    jwt_service: JWTService | None = None,
    device_binding: DeviceBindingService | None = None,
) -> APIRouter:
    jwt = jwt_service or JWT
    binding = device_binding or DeviceBindingService()
    router = APIRouter(prefix="/v1", tags=["pilot-auth"])

    @router.post("/auth/token")
    def create_token(payload: dict[str, Any]) -> dict[str, str]:
        user_id = str(payload.get("user_id", ""))
        role = str(payload.get("role", "OPERATOR")).upper()
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")
        if role not in AUTH_ROLES:
            raise HTTPException(status_code=400, detail="invalid_role")
        return {"token": jwt.create_token(user_id, role=role)}

    @router.post("/devices/register")
    def register_device(payload: dict[str, Any], authorization: str = Header(default="")) -> dict[str, Any]:
        claims = _claims_from_header(jwt, authorization)
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


def _claims_from_header(jwt: JWTService, authorization: str) -> JWTClaims:
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise HTTPException(status_code=401, detail="bearer token required")
    try:
        return jwt.verify_token(authorization[len(prefix) :])
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def get_current_claims(authorization: str = Header(default="")) -> JWTClaims:
    return _claims_from_header(JWT, authorization)


def require_roles(*roles: str):
    allowed = {role.upper() for role in roles}

    def dependency(claims: JWTClaims = Depends(get_current_claims)) -> JWTClaims:
        if allowed and claims.role not in allowed:
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
