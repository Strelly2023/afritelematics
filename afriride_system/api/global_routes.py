"""Public bootstrap and authoritative regional pricing routes."""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from afriride_system.globalization import global_readiness


router = APIRouter(prefix="/v1/global", tags=["global-readiness"])


class QuoteRequest(BaseModel):
    region_id: str
    distance_km: Decimal = Field(ge=0, le=5000)
    duration_minutes: Decimal = Field(ge=0, le=10000)
    surge_multiplier: Decimal = Field(default=Decimal("1"), ge=1, le=10)
    vehicle_multiplier: Decimal = Field(default=Decimal("1"), ge=0.5, le=10)


class ComplianceCheckRequest(BaseModel):
    region_id: str
    actor_type: str = Field(pattern="^(driver|rider|fleet)$")
    documents: list[str] = Field(default_factory=list, max_length=100)


@router.get("/regions")
def regions() -> dict:
    return {"contract": "afriride.global.v1", "items": global_readiness.regions()}


@router.get("/config")
def global_config(
    region_id: str | None = Query(default=None),
    locale: str | None = Query(default=None),
    organization_id: str = Header(default="afritech-core", alias="X-Organization-ID"),
) -> dict:
    try:
        return global_readiness.resolve(
            organization_id=organization_id, region_id=region_id, locale=locale
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/pricing/quote")
def pricing_quote(payload: QuoteRequest) -> dict:
    try:
        return global_readiness.quote(**payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc


@router.post("/compliance/check")
def compliance_check(payload: ComplianceCheckRequest) -> dict:
    try:
        return global_readiness.compliance_check(**payload.model_dump())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
