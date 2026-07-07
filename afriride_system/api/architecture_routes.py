"""Private-development architecture signature route."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from afriride_system.api.auth import JWT
from afriride_system.payments.private_development import ensure_private_development_mode

router = APIRouter(prefix="/v1/architecture", tags=["architecture"])


@router.get("/signature")
def architecture_signature(authorization: str | None = Header(default=None, alias="Authorization")) -> dict:
    _require_token(authorization)
    config = ensure_private_development_mode()
    return {
        "status": "ok",
        "environment": config.environment,
        "signature_algorithm": "Ed25519",
        "signature": "private-development-signature",
        "authority": "architecture_signature",
        "private_development": True,
    }


def _require_token(authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="bearer token required")
    try:
        JWT.verify_token(authorization[len("Bearer ") :])
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

