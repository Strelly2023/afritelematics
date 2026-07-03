"""Production security controls for mobile API traffic."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any
from urllib.request import Request as URLRequest, urlopen

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse


def _production() -> bool:
    return os.environ.get("AFRIRIDE_ENV", "development").lower() in {"prod", "production"}


@dataclass(frozen=True)
class SecurityPolicy:
    replay_window_seconds: int = 300
    challenge_ttl_seconds: int = 120
    rate_window_seconds: int = 60
    anonymous_rate_limit: int = 30
    authenticated_rate_limit: int = 180


POLICY = SecurityPolicy()
_lock = threading.RLock()
_nonces: dict[str, float] = {}
_challenges: dict[str, tuple[str, float]] = {}
_rates: dict[str, deque[float]] = defaultdict(deque)
_sessions: dict[str, dict[str, Any]] = {}


def reset_security_state() -> None:
    with _lock:
        _nonces.clear()
        _challenges.clear()
        _rates.clear()
        _sessions.clear()


def create_attestation_challenge(device_id: str) -> dict[str, Any]:
    if not device_id.strip():
        raise ValueError("device_id_required")
    nonce = secrets.token_urlsafe(32)
    expires_at = time.time() + POLICY.challenge_ttl_seconds
    with _lock:
        _challenges[nonce] = (device_id, expires_at)
    return {
        "nonce": nonce,
        "device_id": device_id,
        "expires_at": int(expires_at),
        "cloud_project_number": os.environ.get("AFRIRIDE_PLAY_CLOUD_PROJECT_NUMBER") or None,
    }


def verify_attestation(payload: dict[str, Any]) -> dict[str, Any]:
    nonce = str(payload.get("nonce", ""))
    device_id = str(payload.get("device_id", ""))
    platform = str(payload.get("platform", "")).lower()
    token = str(payload.get("token", ""))
    with _lock:
        challenge = _challenges.pop(nonce, None)
    if challenge is None:
        raise ValueError("attestation_challenge_missing_or_replayed")
    expected_device, expires_at = challenge
    if expires_at < time.time():
        raise ValueError("attestation_challenge_expired")
    if not hmac.compare_digest(expected_device, device_id):
        raise ValueError("attestation_device_mismatch")
    if platform not in {"android", "ios"}:
        raise ValueError("unsupported_attestation_platform")

    verdict = _verify_provider_token(platform, token, nonce, device_id)
    if not verdict.get("trusted"):
        raise ValueError(str(verdict.get("reason", "device_integrity_failed")))
    session_id = secrets.token_urlsafe(24)
    record = {
        "session_id": session_id,
        "device_id": device_id,
        "platform": platform,
        "integrity": verdict,
        "created_at": int(time.time()),
        "revoked": False,
    }
    with _lock:
        _sessions[session_id] = record
    return record


def _verify_provider_token(
    platform: str, token: str, nonce: str, device_id: str
) -> dict[str, Any]:
    verifier_url = os.environ.get(
        "AFRIRIDE_PLAY_INTEGRITY_VERIFIER_URL"
        if platform == "android"
        else "AFRIRIDE_APP_ATTEST_VERIFIER_URL",
        "",
    )
    if verifier_url:
        body = json.dumps(
            {"token": token, "nonce": nonce, "device_id": device_id, "platform": platform}
        ).encode()
        request = URLRequest(
            verifier_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:  # noqa: S310 - configured trusted endpoint
            result = json.loads(response.read())
        return {
            "trusted": bool(result.get("trusted")),
            "provider": "play_integrity" if platform == "android" else "app_attest",
            "verdicts": result.get("verdicts", []),
            "reason": result.get("reason"),
        }

    if _production():
        return {"trusted": False, "reason": "attestation_verifier_not_configured"}

    expected = hmac.new(
        os.environ.get("AFRIRIDE_DEV_ATTESTATION_SECRET", "afriride-local-attestation").encode(),
        f"{platform}:{device_id}:{nonce}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return {
        "trusted": hmac.compare_digest(token, expected),
        "provider": "development_hmac",
        "verdicts": ["DEVELOPMENT"] if hmac.compare_digest(token, expected) else [],
        "reason": None if hmac.compare_digest(token, expected) else "invalid_attestation",
    }


def revoke_session(session_id: str) -> bool:
    with _lock:
        session = _sessions.get(session_id)
        if session is None:
            return False
        session["revoked"] = True
        session["revoked_at"] = int(time.time())
        return True


def build_security_router() -> APIRouter:
    router = APIRouter(prefix="/v1/security", tags=["security"])

    @router.post("/attestation/challenge")
    def challenge(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return create_attestation_challenge(str(payload.get("device_id", "")))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.post("/attestation/verify")
    def verify(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            return verify_attestation(payload)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    @router.post("/sessions/{session_id}/revoke")
    def revoke(session_id: str) -> dict[str, Any]:
        return {"session_id": session_id, "revoked": revoke_session(session_id)}

    return router


async def security_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    now = time.time()
    client = request.client.host if request.client else "unknown"
    authorization = request.headers.get("Authorization", "")
    identity = hashlib.sha256(authorization.encode()).hexdigest()[:24] if authorization else client
    if _production() or os.environ.get("AFRIRIDE_ENFORCE_RATE_LIMITING") == "true":
        limit = POLICY.authenticated_rate_limit if authorization else POLICY.anonymous_rate_limit
        retry_after = _consume_rate(identity, now, limit)
        if retry_after is not None:
            return _security_error(
                429, "rate_limit_exceeded", headers={"Retry-After": str(retry_after)}
            )

    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and _requires_replay_guard(
        request.url.path
    ):
        error = _validate_replay_headers(request, now)
        if error:
            return _security_error(409 if error == "request_replayed" else 400, error)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = (
        "no-store" if request.url.path.startswith(("/auth", "/v1/auth", "/v1/security")) else "private"
    )
    return response


def _consume_rate(identity: str, now: float, limit: int) -> int | None:
    with _lock:
        bucket = _rates[identity]
        cutoff = now - POLICY.rate_window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            return max(1, int(bucket[0] + POLICY.rate_window_seconds - now))
        bucket.append(now)
    return None


def _requires_replay_guard(path: str) -> bool:
    if path in {"/auth/token", "/v1/auth/token"}:
        return False
    if path == "/v1/security/attestation/challenge":
        return False
    return _production() or os.environ.get("AFRIRIDE_ENFORCE_REPLAY_PROTECTION") == "true"


def _validate_replay_headers(request: Request, now: float) -> str | None:
    timestamp = request.headers.get("X-Request-Timestamp", "")
    nonce = request.headers.get("X-Request-Nonce", "")
    try:
        sent_at = float(timestamp)
    except ValueError:
        return "request_timestamp_required"
    if abs(now - sent_at) > POLICY.replay_window_seconds:
        return "request_timestamp_outside_window"
    if len(nonce) < 24 or len(nonce) > 200:
        return "request_nonce_required"
    key = hashlib.sha256(
        f"{request.method}:{request.url.path}:{nonce}".encode()
    ).hexdigest()
    with _lock:
        expired = [item for item, expiry in _nonces.items() if expiry <= now]
        for item in expired:
            _nonces.pop(item, None)
        if key in _nonces:
            return "request_replayed"
        _nonces[key] = now + POLICY.replay_window_seconds
    return None


def _security_error(
    status: int, code: str, *, headers: dict[str, str] | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code.upper(), "message": code}},
        headers=headers,
    )
