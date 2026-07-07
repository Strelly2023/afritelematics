"""Private-development treasury snapshot route."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from afriride_system.api.auth import JWT
from afriride_system.payments.private_development import ensure_private_development_mode

router = APIRouter(prefix="/v1/treasury", tags=["treasury"])


@router.get("/snapshot")
def treasury_snapshot(authorization: str | None = Header(default=None, alias="Authorization")) -> dict:
    claims = _require_token(authorization)
    config = ensure_private_development_mode()
    return {
        "status": "ok",
        "mode": config.payment_mode,
        "environment": config.environment,
        "simulated": True,
        "liquidity_ratio": 1.0,
        "reserve_headroom_minor": 10000000,
        "prefunding_gap_minor": 0,
        "risk_level": "LOW",
        "treasury_decision": "observe",
        "provider_recommendations": ["maintain simulated ledger only", "keep live payouts disabled"],
        "stress_test_scenarios": ["offline network", "duplicate transfer prevention", "device reboot"],
        "token_subject": claims.sub,
        "token_role": claims.role,
    }


def _require_token(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="bearer token required")
    try:
        return JWT.verify_token(authorization[len("Bearer ") :])
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

