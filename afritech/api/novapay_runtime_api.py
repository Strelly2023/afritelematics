"""Transfer-centric NovaPay runtime API.

This is the governed runtime surface for NovaPay vNext:
- one Transfer domain
- one admission pipeline
- one ledger truth
- one event truth
- many pluggable rails
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Mapping

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.core_platform.models import Identity
from afritech.core_platform.novapay_runtime import (
    DEFAULT_NOVAPAY_RUNTIME,
    NovaPayRuntimeEngine,
    NovaPayTransferAdmissionError,
)


class TransferQuoteRequest(BaseModel):
    transfer_type: str = "Cross-Border Remittance"
    recipient_name: str
    recipient_identifier: str
    recipient_country: str
    amount: Decimal
    source_currency: str = "AUD"
    source_country: str = "AU"
    funding_source_type: str = "wallet"
    funding_source_reference: str
    payout_method: str = "mobile_money"
    use_case: str = "transparent_pricing"
    memo: str | None = None
    recipient_type: str = "individual"
    recipient_id: str | None = None
    recipient_wallet_id: str | None = None
    recipient_bank_account_id: str | None = None
    recipient_mobile_money_id: str | None = None
    live_provider: bool = False

    @model_validator(mode="before")
    @classmethod
    def _reject_float_boundary(cls, data: Any) -> Any:
        if isinstance(data, Mapping):
            for value in data.values():
                if isinstance(value, float):
                    raise ValueError("float_not_allowed")
        return data


class TransferCreateRequest(TransferQuoteRequest):
    auto_execute: bool = True


class FundingSourceValidateRequest(BaseModel):
    funding_source_type: str = "wallet"
    owner_id: str
    provider: str | None = None
    reference: str
    funding_source_id: str | None = None
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)


def _identity_from_claims(claims: JWTClaims) -> Identity:
    return Identity(
        identity_id=claims.sub,
        email=f"{claims.sub}@novapay.local",
        roles=(claims.role,),
        organization_id=claims.organization_id,
        kyc_status="verified",
    )


def _runtime() -> NovaPayRuntimeEngine:
    return DEFAULT_NOVAPAY_RUNTIME


def _translate_error(exc: NovaPayTransferAdmissionError) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


def build_novapay_runtime_router(runtime: NovaPayRuntimeEngine | None = None) -> APIRouter:
    runtime = runtime or _runtime()
    router = APIRouter(tags=["novapay-runtime"])

    readable_roles = require_roles(
        "CUSTOMER",
        "DRIVER",
        "OPERATOR",
        "ADMIN",
        "CLIENT",
        "FLEET_OWNER",
        "PARTNER",
        "VERIFIER",
    )

    privileged_roles = require_roles("OPERATOR", "ADMIN")

    @router.get("/v1/jurisdictions")
    def jurisdictions(claims: JWTClaims = Depends(readable_roles)) -> dict[str, Any]:
        return {
            "view": "novapay_jurisdictions",
            "organization_id": claims.organization_id,
            "jurisdictions": runtime.build_jurisdictions(),
        }

    @router.get("/v1/licenses")
    def licenses(claims: JWTClaims = Depends(readable_roles)) -> dict[str, Any]:
        return {
            "view": "novapay_licenses",
            "organization_id": claims.organization_id,
            "licenses": runtime.build_licenses(),
        }

    @router.get("/v1/corridors")
    def corridors(claims: JWTClaims = Depends(readable_roles)) -> dict[str, Any]:
        return {
            "view": "novapay_corridors",
            "organization_id": claims.organization_id,
            "corridors": runtime.build_corridors(),
        }

    @router.post("/v1/funding-sources/validate")
    def validate_funding_source(
        body: FundingSourceValidateRequest,
        claims: JWTClaims = Depends(readable_roles),
    ) -> dict[str, Any]:
        try:
            funding_source = runtime.validate_funding_source(
                {
                    **body.model_dump(),
                    "owner_id": body.owner_id or claims.sub,
                }
            )
        except NovaPayTransferAdmissionError as exc:
            raise _translate_error(exc)
        return {
            "view": "novapay_funding_source_validation",
            "organization_id": claims.organization_id,
            "funding_source": funding_source,
        }

    @router.post("/v1/transfers/quote")
    def quote_transfer(
        body: TransferQuoteRequest,
        claims: JWTClaims = Depends(readable_roles),
    ) -> dict[str, Any]:
        identity = _identity_from_claims(claims)
        try:
            admission = runtime.admit_transfer(
                {
                    **body.model_dump(),
                    "sender_id": claims.sub,
                    "organization_id": claims.organization_id,
                },
                identity=identity,
            )
        except NovaPayTransferAdmissionError as exc:
            raise _translate_error(exc)
        return {
            "view": "novapay_transfer_quote",
            "organization_id": claims.organization_id,
            "transfer_id": admission.transfer_id,
            "transfer": {
                "transfer_type": admission.transfer_type,
                "sender": admission.sender,
                "recipient": admission.recipient,
                "funding_source": admission.funding_source,
                "jurisdiction": admission.jurisdiction,
                "license": admission.license,
                "corridor": admission.corridor,
                "compliance": admission.compliance,
                "policy": admission.policy,
                "quote": admission.quote,
                "routing": admission.routing,
                "decision_trace": admission.decision_trace,
            },
        }

    @router.post("/v1/transfers")
    def create_transfer(
        body: TransferCreateRequest,
        claims: JWTClaims = Depends(readable_roles),
    ) -> dict[str, Any]:
        identity = _identity_from_claims(claims)
        try:
            record = runtime.create_transfer(
                {
                    **body.model_dump(),
                    "sender_id": claims.sub,
                    "organization_id": claims.organization_id,
                },
                identity=identity,
                auto_execute=body.auto_execute,
                live_provider=body.live_provider,
            )
        except NovaPayTransferAdmissionError as exc:
            raise _translate_error(exc)
        return {
            "view": "novapay_transfer",
            "organization_id": claims.organization_id,
            "transfer_id": record.transfer.transfer_id,
            "transfer": record.transfer.canonical(),
            "admission": record.admission.canonical(),
            "funding_source": record.funding_source.canonical(),
            "recipient": record.recipient.canonical(),
            "compliance_case": record.compliance_case.canonical(),
            "ledger_entries": [entry.canonical() for entry in record.ledger_entries],
            "settlement": record.settlement.canonical() if record.settlement else None,
            "receipt": record.receipt.canonical() if record.receipt else None,
            "events": [event.canonical() for event in record.events],
        }

    @router.post("/v1/transfers/{transfer_id}/execute")
    def execute_transfer(
        transfer_id: str,
        claims: JWTClaims = Depends(privileged_roles),
    ) -> dict[str, Any]:
        identity = _identity_from_claims(claims)
        try:
            record = runtime.execute_transfer(
                transfer_id,
                identity=identity,
                live_provider=bool(getattr(claims, "role", "") == "ADMIN"),
            )
        except NovaPayTransferAdmissionError as exc:
            raise _translate_error(exc)
        return {
            "view": "novapay_transfer_execution",
            "organization_id": claims.organization_id,
            "transfer_id": record.transfer.transfer_id,
            "transfer": record.transfer.canonical(),
            "settlement": record.settlement.canonical() if record.settlement else None,
            "receipt": record.receipt.canonical() if record.receipt else None,
            "verification": runtime.verify_receipt(transfer_id),
        }

    @router.get("/v1/transfers/{transfer_id}")
    def get_transfer(
        transfer_id: str,
        claims: JWTClaims = Depends(readable_roles),
    ) -> dict[str, Any]:
        try:
            record = runtime.get_transfer(transfer_id)
        except NovaPayTransferAdmissionError as exc:
            raise _translate_error(exc)
        if record is None:
            raise HTTPException(status_code=404, detail=f"transfer_not_found:{transfer_id}")
        return {
            "view": "novapay_transfer_detail",
            "organization_id": claims.organization_id,
            "transfer_id": transfer_id,
            "transfer": record.transfer.canonical(),
            "admission": record.admission.canonical(),
            "funding_source": record.funding_source.canonical(),
            "recipient": record.recipient.canonical(),
            "compliance_case": record.compliance_case.canonical(),
            "ledger_entries": [entry.canonical() for entry in record.ledger_entries],
            "settlement": record.settlement.canonical() if record.settlement else None,
            "receipt": record.receipt.canonical() if record.receipt else None,
            "verification": runtime.verify_receipt(transfer_id) if record.receipt else None,
        }

    @router.get("/v1/transfers/{transfer_id}/receipt")
    def get_receipt(
        transfer_id: str,
        claims: JWTClaims = Depends(readable_roles),
    ) -> dict[str, Any]:
        try:
            receipt = runtime.get_receipt(transfer_id)
        except NovaPayTransferAdmissionError as exc:
            raise _translate_error(exc)
        return {
            "view": "novapay_transfer_receipt",
            "organization_id": claims.organization_id,
            "transfer_id": transfer_id,
            "receipt": receipt,
        }

    @router.get("/v1/transfers/{transfer_id}/verification")
    def verify_transfer_receipt(
        transfer_id: str,
        claims: JWTClaims = Depends(readable_roles),
    ) -> dict[str, Any]:
        try:
            verification = runtime.verify_receipt(transfer_id)
        except NovaPayTransferAdmissionError as exc:
            raise _translate_error(exc)
        return {
            "view": "novapay_transfer_verification",
            "organization_id": claims.organization_id,
            **verification,
        }

    @router.get("/v1/transfers/{transfer_id}/timeline")
    def transfer_timeline(
        transfer_id: str,
        claims: JWTClaims = Depends(readable_roles),
    ) -> dict[str, Any]:
        try:
            timeline = runtime.get_timeline(transfer_id)
        except NovaPayTransferAdmissionError as exc:
            raise _translate_error(exc)
        return {
            "view": "novapay_transfer_timeline",
            "organization_id": claims.organization_id,
            "transfer_id": transfer_id,
            "timeline": timeline,
        }

    return router


__all__ = ["build_novapay_runtime_router"]
