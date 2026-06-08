"""Pilot JWT authentication and role enforcement for AfriRide."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse


ROLES = frozenset({"RIDER", "DRIVER", "OPERATOR"})


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


class JWTService:
    def __init__(self, secret: str, ttl_seconds: int = 12 * 60 * 60) -> None:
        if not secret:
            raise ValueError("secret must be non-empty")
        self.secret = secret.encode("utf-8")
        self.ttl_seconds = ttl_seconds

    def create_token(self, user_id: str, role: str, *, issued_at: int | None = None) -> str:
        if role not in ROLES:
            raise ValueError("invalid_role")
        now = int(time.time()) if issued_at is None else issued_at
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"sub": user_id, "role": role, "exp": now + self.ttl_seconds}
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
        role = str(payload.get("role", ""))
        if role not in ROLES:
            raise ValueError("invalid_role")
        return AuthClaims(sub=str(payload["sub"]), role=role, exp=int(payload["exp"]))


JWT = JWTService(os.environ.get("AFRIRIDE_JWT_SECRET", "afriride-pilot-secret"))


def build_auth_router(jwt_service: JWTService = JWT) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["auth"])

    @router.post("/token")
    def create_token(payload: dict[str, Any]) -> dict[str, str]:
        user_id = str(payload.get("user_id", "")).strip()
        role = str(payload.get("role", "")).strip().upper()
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id required")
        if role not in ROLES:
            raise HTTPException(status_code=400, detail="invalid_role")
        return {"token": jwt_service.create_token(user_id, role)}

    return router


async def auth_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    required_roles = _required_roles(request.method, request.url.path)
    if required_roles is None:
        return await call_next(request)

    authorization = request.headers.get("Authorization", "")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return _auth_error(401, "bearer token required")

    try:
        claims = JWT.verify_token(authorization[len(prefix) :])
    except ValueError as exc:
        return _auth_error(401, str(exc))

    if claims.role not in required_roles:
        return _auth_error(403, "insufficient_role")

    request.state.auth_claims = claims
    return await call_next(request)


def _required_roles(method: str, path: str) -> set[str] | None:
    if method == "OPTIONS":
        return None
    if path in {"/", "/health"} or path.startswith("/auth/"):
        return None
    if path.startswith("/system/") or path == "/rides/active":
        return {"OPERATOR"}
    if path.startswith("/passenger/"):
        return {"RIDER", "OPERATOR"} if method == "GET" else {"RIDER"}
    if path.startswith("/driver/"):
        return {"DRIVER", "OPERATOR"} if method == "GET" else {"DRIVER"}
    if path.startswith("/ride/"):
        if method == "POST":
            return {"DRIVER"}
        return {"RIDER", "DRIVER", "OPERATOR"}
    return None


def _auth_error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": message.upper(),
                "message": message,
            }
        },
    )
