"""NovaPay ecosystem API surfaces."""

from __future__ import annotations

from decimal import Decimal
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, model_validator

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.novapay import NovaPayEcosystem, NovaPayRepository


def _service() -> NovaPayEcosystem:
    db_path = Path(os.environ.get("NOVAPAY_DB_PATH", ":memory:"))
    return NovaPayEcosystem(NovaPayRepository(db_path))


class StrictPayload(BaseModel):
    @model_validator(mode="before")
    @classmethod
    def _reject_float_boundary(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for value in data.values():
                if isinstance(value, float):
                    raise ValueError("float_not_allowed")
        return data


class WalletCreateRequest(StrictPayload):
    owner_id: str
    organization_id: str
    currency: str = "AUD"
    owner_type: str = "consumer"
    initial_balance: Decimal = Decimal("0")
    kyc_status: str = "pending"
    display_name: str | None = None


class TransferRequest(StrictPayload):
    organization_id: str
    actor_id: str
    actor_role: str
    sender_wallet_id: str
    receiver_wallet_id: str
    amount: Decimal
    currency: str = "AUD"
    transfer_type: str = "transfer"
    idempotency_key: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class QrPaymentRequest(StrictPayload):
    organization_id: str
    actor_id: str
    actor_role: str
    payer_wallet_id: str
    merchant_wallet_id: str
    amount: Decimal
    currency: str = "AUD"
    qr_code: str
    idempotency_key: str


class RefundRequest(StrictPayload):
    organization_id: str
    actor_id: str
    actor_role: str
    source_wallet_id: str
    destination_wallet_id: str
    amount: Decimal
    currency: str = "AUD"
    reason: str = "customer_request"
    idempotency_key: str


class DisputeRequest(StrictPayload):
    organization_id: str
    actor_id: str
    actor_role: str
    transaction_id: str
    reason: str
    idempotency_key: str


class PayoutRequest(StrictPayload):
    organization_id: str
    actor_id: str
    actor_role: str
    source_wallet_id: str
    destination_reference: str
    amount: Decimal
    currency: str = "AUD"
    scheduled_for: str | None = None
    idempotency_key: str


class PayrollLineItem(StrictPayload):
    recipient_wallet_id: str
    amount: Decimal
    note: str | None = None


class PayrollRequest(StrictPayload):
    organization_id: str
    actor_id: str
    actor_role: str
    source_wallet_id: str
    currency: str = "AUD"
    payroll: list[PayrollLineItem]
    idempotency_key: str


class AgentCashRequest(StrictPayload):
    organization_id: str
    actor_id: str
    actor_role: str
    wallet_id: str
    amount: Decimal
    currency: str = "AUD"
    direction: str = Field(pattern="^(in|out)$")
    idempotency_key: str


class DeveloperAppRequest(StrictPayload):
    organization_id: str
    developer_id: str
    app_name: str
    webhook_url: str


class ComplianceHoldRequest(StrictPayload):
    organization_id: str
    actor_id: str
    subject_id: str
    reason: str


class InvoiceRequest(StrictPayload):
    organization_id: str
    actor_id: str
    actor_role: str
    customer_wallet_id: str
    amount: Decimal
    currency: str = "AUD"
    reference: str
    due_date: str | None = None
    idempotency_key: str


class WebhookRequest(StrictPayload):
    organization_id: str
    developer_id: str
    webhook_url: str
    event_types: list[str] = Field(default_factory=list)
    secret_hint: str | None = None


class IdentityRequest(StrictPayload):
    identity_id: str
    identity_type: str
    organization_id: str
    email: str | None = None
    display_name: str | None = None
    kyc_status: str = "pending"
    mfa_ready: bool = False
    roles: list[str] = Field(default_factory=list)


def build_novapay_ecosystem_router(service: NovaPayEcosystem | None = None) -> APIRouter:
    ecosystem = service or _service()
    router = APIRouter(prefix="/v1/novapay", tags=["novapay"])

    readable = require_roles(
        "CUSTOMER",
        "CLIENT",
        "PARTNER",
        "SUPPLIER",
        "DISPATCHER",
        "OPERATOR",
        "ADMIN",
        "DEVELOPER",
        "VERIFIER",
        "OBSERVER",
        "INVESTOR",
        "FLEET_OWNER",
    )
    internal = require_roles("OPERATOR", "ADMIN")
    developer = require_roles("DEVELOPER", "OPERATOR", "ADMIN")
    trust_roles = require_roles("VERIFIER", "OBSERVER", "OPERATOR", "ADMIN")
    finance_roles = require_roles("OPERATOR", "ADMIN", "INVESTOR")

    @router.post("/identities")
    def identities(payload: IdentityRequest, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.register_identity(**payload.model_dump())

    @router.post("/wallets")
    def create_wallet(payload: WalletCreateRequest, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.create_wallet(
            owner_id=payload.owner_id,
            organization_id=payload.organization_id,
            currency=payload.currency,
            owner_type=payload.owner_type,
            initial_balance=payload.initial_balance,
            kyc_status=payload.kyc_status,
            metadata={"display_name": payload.display_name, "requested_by": claims.sub},
        )

    @router.get("/wallets/{wallet_id}")
    def wallet(wallet_id: str, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.wallet(wallet_id) or {"wallet_id": wallet_id, "status": "not_found"}

    @router.post("/transfers")
    def transfer(payload: TransferRequest, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.transfer_money(**payload.model_dump())

    @router.post("/qr")
    def qr(payload: QrPaymentRequest, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.qr_payment(**payload.model_dump())

    @router.post("/merchants")
    def merchant_payment(payload: TransferRequest, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        data = payload.model_dump()
        return ecosystem.merchant_payment(**data)

    @router.get("/merchants")
    def merchants(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.merchant_app_surface(organization_id=claims.organization_id)

    @router.post("/bills")
    def bill_payment(payload: TransferRequest, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        data = payload.model_dump()
        return ecosystem.bill_payment(**data)

    @router.get("/bills")
    def bills(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_bills",
            "organization_id": claims.organization_id,
            "invoices": ecosystem.repository.list("novapay_invoices", organization_id=claims.organization_id),
        }

    @router.post("/remittances")
    def remittance(payload: TransferRequest, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        data = payload.model_dump()
        return ecosystem.remittance(**data)

    @router.post("/cards")
    def card(payload: TransferRequest, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        data = payload.model_dump()
        return ecosystem.card_payment(**data)

    @router.get("/cards")
    def cards(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_cards",
            "organization_id": claims.organization_id,
            "cards": [
                {"type": "virtual", "status": "active"},
                {"type": "physical", "status": "active"},
                {"type": "disposable", "status": "supported"},
            ],
        }

    @router.post("/payouts")
    def payouts(payload: PayoutRequest, claims: JWTClaims = Depends(internal)) -> dict[str, Any]:
        return ecosystem.payout(**payload.model_dump())

    @router.post("/operations/payroll")
    def payroll(payload: PayrollRequest, claims: JWTClaims = Depends(internal)) -> dict[str, Any]:
        return ecosystem.business_payroll(
            organization_id=payload.organization_id,
            actor_id=payload.actor_id,
            actor_role=payload.actor_role,
            source_wallet_id=payload.source_wallet_id,
            recipients=[item.model_dump() for item in payload.payroll],
            currency=payload.currency,
            idempotency_key=payload.idempotency_key,
        )

    @router.post("/payroll")
    def payroll_alias(payload: PayrollRequest, claims: JWTClaims = Depends(internal)) -> dict[str, Any]:
        return ecosystem.business_payroll(
            organization_id=payload.organization_id,
            actor_id=payload.actor_id,
            actor_role=payload.actor_role,
            source_wallet_id=payload.source_wallet_id,
            recipients=[item.model_dump() for item in payload.payroll],
            currency=payload.currency,
            idempotency_key=payload.idempotency_key,
        )

    @router.post("/settlements")
    def settlement(payload: DisputeRequest, claims: JWTClaims = Depends(internal)) -> dict[str, Any]:
        return ecosystem.settle(
            organization_id=payload.organization_id,
            transaction_id=payload.transaction_id,
            actor_id=payload.actor_id,
            actor_role=payload.actor_role,
        )

    @router.post("/reconciliation")
    def reconciliation(payload: dict[str, Any], claims: JWTClaims = Depends(finance_roles)) -> dict[str, Any]:
        return ecosystem.reconcile(
            organization_id=str(payload["organization_id"]),
            batch_name=str(payload.get("batch_name", "daily")),
            actor_id=claims.sub,
            actor_role=claims.role,
        )

    @router.post("/refunds")
    def refunds(payload: RefundRequest, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.refund(**payload.model_dump())

    @router.post("/disputes")
    def disputes(payload: DisputeRequest, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.dispute(**payload.model_dump())

    @router.post("/agent/cash")
    def agent_cash(payload: AgentCashRequest, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.agent_cash_movement(**payload.model_dump())

    @router.get("/agents")
    def agents(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.agent_app_surface(organization_id=claims.organization_id)

    @router.get("/agents/profile")
    def agent_profile(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.agent_profile_surface(organization_id=claims.organization_id)

    @router.get("/agents/float")
    def agent_float(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.agent_float_surface(organization_id=claims.organization_id)

    @router.post("/agents/send-money")
    def agent_send_money(payload: dict[str, Any], claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_agent_send_money",
            "organization_id": claims.organization_id,
            "status": "preview",
            "policy": "NovaPower required",
            "receipt": "NovaTrust preview only",
            "payload": payload,
        }

    @router.post("/agents/receive-money")
    def agent_receive_money(payload: dict[str, Any], claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_agent_receive_money",
            "organization_id": claims.organization_id,
            "status": "preview",
            "policy": "NovaPower required",
            "payload": payload,
        }

    @router.post("/agents/cash-in")
    def agent_cash_in(payload: dict[str, Any], claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_agent_cash_in",
            "organization_id": claims.organization_id,
            "status": "preview",
            "policy": "NovaPower required",
            "payload": payload,
        }

    @router.post("/agents/cash-out")
    def agent_cash_out(payload: dict[str, Any], claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_agent_cash_out",
            "organization_id": claims.organization_id,
            "status": "preview",
            "policy": "NovaPower required",
            "payload": payload,
        }

    @router.get("/agents/qr")
    def agent_qr(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_agent_qr",
            "organization_id": claims.organization_id,
            "scan_modes": ["camera", "flashlight", "offline_decode"],
        }

    @router.get("/agents/kyc")
    def agent_kyc(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_agent_kyc",
            "organization_id": claims.organization_id,
            "customers": ecosystem.repository.list("novapay_accounts", organization_id=claims.organization_id),
        }

    @router.get("/agents/commissions")
    def agent_commissions(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.agent_float_surface(organization_id=claims.organization_id)

    @router.get("/agents/settlement")
    def agent_settlement(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_agent_settlement",
            "organization_id": claims.organization_id,
            "settlements": ecosystem.repository.list("novapay_settlements", organization_id=claims.organization_id),
        }

    @router.get("/agents/history")
    def agent_history(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.agent_history_surface(organization_id=claims.organization_id)

    @router.get("/agents/offline-queue")
    def agent_offline_queue(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.agent_offline_queue_surface(organization_id=claims.organization_id)

    @router.post("/agents/sync")
    def agent_sync(payload: dict[str, Any], claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_agent_sync",
            "organization_id": claims.organization_id,
            "status": "queued",
            "sync_status": "queued",
            "payload": payload,
            "policy": "NovaPower conflict detection required",
        }

    @router.get("/agents/compliance")
    def agent_compliance(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.agent_compliance_surface(organization_id=claims.organization_id)

    @router.get("/agents/receipts")
    def agent_receipts(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.agent_receipts_surface(organization_id=claims.organization_id)

    @router.get("/agents/supervisor-review")
    def agent_supervisor_review(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.agent_supervisor_review_surface(organization_id=claims.organization_id)

    @router.get("/business")
    def business(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.business_wallet_surface(organization_id=claims.organization_id)

    @router.get("/corporate")
    def corporate(claims: JWTClaims = Depends(internal)) -> dict[str, Any]:
        return ecosystem.corporate_portal_surface(organization_id=claims.organization_id)

    @router.get("/invoices")
    def invoices(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_invoices",
            "invoices": ecosystem.repository.list("novapay_invoices", organization_id=claims.organization_id),
        }

    @router.post("/invoices")
    def create_invoice(payload: InvoiceRequest, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.issue_invoice(**payload.model_dump())

    @router.get("/receipts/{receipt_id}")
    def receipts(receipt_id: str, claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.verify_receipt(receipt_id)

    @router.get("/trust/explorer/{receipt_id}")
    def trust_explorer(receipt_id: str, claims: JWTClaims = Depends(trust_roles)) -> dict[str, Any]:
        return ecosystem.trust_explorer(receipt_id)

    @router.post("/developer/apps")
    def developer_apps(payload: DeveloperAppRequest, claims: JWTClaims = Depends(developer)) -> dict[str, Any]:
        return ecosystem.developer_app_lifecycle(**payload.model_dump())

    @router.get("/webhooks")
    def webhooks(claims: JWTClaims = Depends(developer)) -> dict[str, Any]:
        return {
            "view": "novapay_webhooks",
            "webhooks": ecosystem.repository.list("novapay_webhooks", organization_id=claims.organization_id),
        }

    @router.post("/webhooks")
    def register_webhook(payload: WebhookRequest, claims: JWTClaims = Depends(developer)) -> dict[str, Any]:
        return ecosystem.register_webhook(**payload.model_dump())

    @router.post("/developer/webhooks")
    def developer_webhooks(payload: WebhookRequest, claims: JWTClaims = Depends(developer)) -> dict[str, Any]:
        return ecosystem.register_webhook(**payload.model_dump())

    @router.post("/compliance/holds")
    def compliance_holds(payload: ComplianceHoldRequest, claims: JWTClaims = Depends(internal)) -> dict[str, Any]:
        return ecosystem.compliance_hold(**payload.model_dump())

    @router.get("/finance")
    def finance(claims: JWTClaims = Depends(finance_roles)) -> dict[str, Any]:
        return ecosystem.finance_report(organization_id=claims.organization_id)

    @router.get("/operations")
    def operations(claims: JWTClaims = Depends(internal)) -> dict[str, Any]:
        return ecosystem.operations_dashboard(organization_id=claims.organization_id)

    @router.get("/developer")
    def developer_portal(claims: JWTClaims = Depends(developer)) -> dict[str, Any]:
        return ecosystem.developer_portal_surface(organization_id=claims.organization_id)

    @router.get("/trust")
    def trust_portal(claims: JWTClaims = Depends(trust_roles)) -> dict[str, Any]:
        return {
            "view": "novapay_trust_portal",
            "recent_receipts": ecosystem.repository.list("novapay_receipts", organization_id=claims.organization_id),
            "recent_audit_events": ecosystem.repository.list("novapay_audit_events", organization_id=claims.organization_id),
            "trust_surfaces": ecosystem.trust_surfaces(),
        }

    @router.get("/portals")
    def portals(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_portals",
            "portals": ecosystem.portals(),
            "role_permissions": ecosystem.role_permissions(),
        }

    @router.get("/apps")
    def apps(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return {
            "view": "novapay_app_suite",
            "apps": ecosystem.app_surfaces(),
            "trust": ecosystem.trust_surfaces(),
        }

    @router.get("/ai/insights")
    def insights(claims: JWTClaims = Depends(readable)) -> dict[str, Any]:
        return ecosystem.ai_insights(organization_id=claims.organization_id)

    return router
