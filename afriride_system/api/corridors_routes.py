"""Versioned corridor snapshot route for internal QA validation."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from afriride_system.api.auth import JWT


router = APIRouter(prefix="/v1", tags=["corridors"])


@router.get("/corridors")
def corridors(authorization: str | None = Header(default=None, alias="Authorization")) -> dict:
    _require_token(authorization)
    return {
        "contract": "afriride.global.v1",
        "items": [
            {"origin": "Australia", "destination": "DR Congo", "status": "active"},
            {"origin": "United States", "destination": "DR Congo", "status": "active"},
            {"origin": "Canada", "destination": "DR Congo", "status": "active"},
            {"origin": "United Kingdom", "destination": "DR Congo", "status": "active"},
        ],
    }


def _require_token(authorization: str | None) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="bearer token required")
    try:
        JWT.verify_token(authorization[len("Bearer ") :])
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
