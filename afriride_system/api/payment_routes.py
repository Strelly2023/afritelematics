"""Provider-neutral Phase 6 payment API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from afriride_system.api.dependencies.runtime import get_gateway
from afriride_system.payments.modern import PaymentRepository, default_payment_service

router = APIRouter(prefix="/v1/payments", tags=["payments"])


class ChargeRequest(BaseModel):
    payer_id: str
    ride_id: str | None = None
    driver_id: str | None = None
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    method: str = Field(pattern="^(card|wallet|cash|regional|split)$")
    provider: str = Field(pattern="^(stripe|flutterwave|cash|wallet)$")
    promotion_code: str | None = None


class RefundRequest(BaseModel):
    amount_minor: int = Field(gt=0)


class DisputeRequest(BaseModel):
    opened_by: str
    reason: str = Field(min_length=3, max_length=1000)


class PromotionRequest(BaseModel):
    code: str
    credit_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    uses: int = Field(gt=0)


class PayoutRequest(BaseModel):
    driver_id: str
    amount_minor: int = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    scheduled_for: str


@router.post("/charges")
def charge(payload: ChargeRequest, idempotency_key: str = Header(alias="Idempotency-Key"),
           gateway=Depends(get_gateway)):
    try:
        return default_payment_service(gateway.storage).charge(
            idempotency_key=idempotency_key, **payload.model_dump()
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/transactions/{transaction_id}/refunds")
def refund(transaction_id: str, payload: RefundRequest, gateway=Depends(get_gateway)):
    try:
        return default_payment_service(gateway.storage).refund(transaction_id, payload.amount_minor)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/wallets/{owner_type}/{owner_id}/{currency}")
def wallet(owner_type: str, owner_id: str, currency: str, gateway=Depends(get_gateway)):
    if owner_type not in {"rider", "driver"}:
        raise HTTPException(status_code=400, detail="invalid_wallet_owner_type")
    return PaymentRepository(gateway.storage).wallet(owner_id, owner_type, currency)


@router.post("/transactions/{transaction_id}/disputes")
def dispute(transaction_id: str, payload: DisputeRequest, gateway=Depends(get_gateway)):
    repository = PaymentRepository(gateway.storage)
    if not repository.transaction(transaction_id):
        raise HTTPException(status_code=404, detail="transaction_not_found")
    return repository.create_dispute(transaction_id, payload.opened_by, payload.reason)


@router.post("/promotions")
def promotion(payload: PromotionRequest, gateway=Depends(get_gateway)):
    return PaymentRepository(gateway.storage).create_promotion(**payload.model_dump())


@router.post("/payouts")
def payout(payload: PayoutRequest, gateway=Depends(get_gateway)):
    return PaymentRepository(gateway.storage).schedule_payout(**payload.model_dump())


@router.get("/reporting")
def reporting(gateway=Depends(get_gateway)):
    return PaymentRepository(gateway.storage).report()


@router.get("/health")
def payment_health(gateway=Depends(get_gateway)):
    return PaymentRepository(gateway.storage).health()
