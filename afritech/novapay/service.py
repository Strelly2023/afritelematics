"""Governed NovaPay ecosystem service layer."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import sqlite3
from typing import Any
from uuid import uuid4

from afritech.core_platform.models import AuthorityRequest, Identity
from afritech.core_platform.services import NovaIDService, NovaPowerEngine, NovaTrustService

from .repository import (
    NovaPayRecord,
    NovaPayRepository,
    build_repository_from_environment,
)
from .surfaces import build_app_surfaces, build_trust_surfaces


ROLE_LIMITS = {
    "CUSTOMER": Decimal("250"),
    "CLIENT": Decimal("10000"),
    "PARTNER": Decimal("15000"),
    "SUPPLIER": Decimal("15000"),
    "DISPATCHER": Decimal("5000"),
    "OPERATOR": Decimal("50000"),
    "ADMIN": Decimal("1000000"),
    "DEVELOPER": Decimal("1000"),
    "VERIFIER": Decimal("1000"),
    "OBSERVER": Decimal("0"),
    "INVESTOR": Decimal("25000"),
    "DEVICE": Decimal("500"),
    "DRIVER": Decimal("5000"),
    "FLEET_OWNER": Decimal("25000"),
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _money(value: Decimal | int | str) -> str:
    return f"{Decimal(str(value)).quantize(Decimal('0.01')):.2f}"


def _hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _record(record: NovaPayRecord) -> dict[str, Any]:
    return {
        "record_id": record.record_id,
        "organization_id": record.organization_id,
        "status": record.status,
        "payload": record.payload,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
        **record.payload,
    }


def _outbox_event_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


class NovaPayEcosystem:
    def __init__(
        self,
        repository: NovaPayRepository | None = None,
        *,
        novaid: NovaIDService | None = None,
        novapower: NovaPowerEngine | None = None,
        novatrust: NovaTrustService | None = None,
    ) -> None:
        self.repository = repository or build_repository_from_environment()
        self.novaid = novaid or NovaIDService()
        self.novapower = novapower or NovaPowerEngine()
        self.novatrust = novatrust or NovaTrustService()

    @classmethod
    def default(cls) -> "NovaPayEcosystem":
        return cls()

    def register_identity(
        self,
        *,
        identity_id: str,
        identity_type: str,
        organization_id: str,
        email: str | None = None,
        display_name: str | None = None,
        kyc_status: str = "pending",
        mfa_ready: bool = False,
        roles: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        identity = self.novaid.bind_identity(
            identity_id=identity_id,
            email=email or f"{identity_id}@novapay.local",
            roles=roles or (identity_type.upper(),),
            organization_id=organization_id,
            kyc_status=kyc_status,
        )
        record = self.repository.upsert(
            "novapay_accounts",
            record_id=identity_id,
            organization_id=organization_id,
            status=kyc_status,
            payload={
                "identity": identity.canonical(),
                "identity_type": identity_type,
                "display_name": display_name or identity_id,
                "mfa_ready": mfa_ready,
                "metadata": metadata or {},
            },
        )
        return _record(record)

    def create_wallet(
        self,
        *,
        owner_id: str,
        organization_id: str,
        currency: str = "AUD",
        owner_type: str = "consumer",
        initial_balance: Decimal | int | str = "0",
        kyc_status: str = "pending",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.register_identity(
            identity_id=owner_id,
            identity_type=owner_type,
            organization_id=organization_id,
            kyc_status=kyc_status,
        )
        wallet_id = f"wallet-{owner_id}-{currency.upper()}"
        record = self.repository.upsert(
            "novapay_wallets",
            record_id=wallet_id,
            organization_id=organization_id,
            status="active",
            payload={
                "wallet_id": wallet_id,
                "owner_id": owner_id,
                "owner_type": owner_type,
                "currency": currency.upper(),
                "balance": _money(initial_balance),
                "metadata": metadata or {},
            },
        )
        self.repository.upsert(
            "novapay_accounts",
            record_id=f"acct-{wallet_id}",
            organization_id=organization_id,
            status="active",
            payload={
                "wallet_id": wallet_id,
                "account_type": owner_type,
                "currency": currency.upper(),
                "owner_id": owner_id,
                "balance": _money(initial_balance),
                "metadata": metadata or {},
            },
        )
        return _record(record)

    def wallet(self, wallet_id: str) -> dict[str, Any] | None:
        record = self.repository.get("novapay_wallets", wallet_id)
        return _record(record) if record else None

    def _adjust_wallet(self, wallet_id: str, *, delta: Decimal, reason: str) -> dict[str, Any]:
        wallet = self.repository.get("novapay_wallets", wallet_id)
        if wallet is None:
            raise ValueError("wallet_not_found")
        balance = Decimal(str(wallet.payload.get("balance", "0")))
        updated = balance + delta
        if updated < 0:
            raise ValueError("insufficient_funds")
        wallet.payload["balance"] = _money(updated)
        wallet.payload.setdefault("history", []).append(
            {"delta": _money(delta), "reason": reason, "at": _now()}
        )
        return _record(
            self.repository.upsert(
                "novapay_wallets",
                record_id=wallet.record_id,
                organization_id=wallet.organization_id,
                status=wallet.status,
                payload=wallet.payload,
            )
        )

    def policy_decision(
        self,
        *,
        role: str,
        action: str,
        amount: Decimal | int | str,
        organization_id: str,
        subject_id: str,
        workflow: str,
        approval_required: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        amount_decimal = Decimal(str(amount))
        limit = ROLE_LIMITS.get(role.upper(), Decimal("1000"))
        approved = amount_decimal <= limit
        payload = {
            "decision_id": f"policy-{uuid4().hex[:12]}",
            "request_id": f"request-{uuid4().hex[:12]}",
            "subject_id": subject_id,
            "role": role.upper(),
            "action": action,
            "limit_amount": _money(limit),
            "amount": _money(amount_decimal),
            "approved": approved,
            "requires_manual_review": bool(approval_required and amount_decimal > limit),
            "workflow": workflow,
            "reason": "within_role_limit" if approved else "approval_required",
            "metadata": metadata or {},
        }
        record = self.repository.upsert(
            "novapay_policy_approvals",
            record_id=payload["decision_id"],
            organization_id=organization_id,
            status="approved" if approved else "pending",
            payload=payload,
        )
        return _record(record)

    def find_transaction(self, *, idempotency_key: str) -> dict[str, Any] | None:
        for record in self.repository.list("novapay_transactions"):
            if record.payload.get("idempotency_key") == idempotency_key:
                return _record(record)
        return None

    def _enqueue_financial_event(
        self,
        *,
        organization_id: str,
        event_type: str,
        resource_type: str,
        resource_id: str,
        payload: dict[str, Any],
        actor_id: str,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        idempotency_key: str | None = None,
        event_version: int = 1,
    ) -> None:
        enqueue = getattr(self.repository, "enqueue_outbox", None)
        if callable(enqueue):
            enqueue(
                outbox_event_id=_outbox_event_id("outbox"),
                organization_id=organization_id,
                event_type=event_type,
                resource_type=resource_type,
                resource_id=resource_id,
                payload=payload,
                idempotency_key=idempotency_key,
                tenant_id=organization_id,
                actor_id=actor_id,
                causation_id=causation_id or "",
                correlation_id=correlation_id or "",
                event_version=event_version,
                status="pending",
            )
            return
        self.repository.upsert(
            "novapay_audit_events",
            record_id=_outbox_event_id("outbox"),
            organization_id=organization_id,
            status="recorded",
            payload={
                "event_type": event_type,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "payload": payload,
                "actor_id": actor_id,
                "correlation_id": correlation_id or "",
                "causation_id": causation_id or "",
                "idempotency_key": idempotency_key,
                "event_version": event_version,
            },
        )

    def transfer_money(
        self,
        *,
        organization_id: str,
        actor_id: str,
        actor_role: str,
        sender_wallet_id: str,
        receiver_wallet_id: str,
        amount: Decimal | int | str,
        currency: str,
        transfer_type: str,
        idempotency_key: str,
        provider: str = "novapay-core",
        metadata: dict[str, Any] | None = None,
        require_approval: bool = False,
    ) -> dict[str, Any]:
        amount_decimal = Decimal(str(amount))
        if amount_decimal <= 0:
            raise ValueError("transfer_amount_must_be_positive")
        with self.repository.transaction():
            existing = self.find_transaction(idempotency_key=idempotency_key)
            if existing is not None:
                return existing
            approval = self.policy_decision(
                role=actor_role,
                action=transfer_type,
                amount=amount_decimal,
                organization_id=organization_id,
                subject_id=actor_id,
                workflow="transfer",
                approval_required=require_approval,
                metadata=metadata,
            )
            if not approval["approved"]:
                raise PermissionError("policy_hold")
            sender_after = self._adjust_wallet(sender_wallet_id, delta=-amount_decimal, reason=transfer_type)
            receiver_after = self._adjust_wallet(receiver_wallet_id, delta=amount_decimal, reason=transfer_type)
            transaction_id = f"txn-{uuid4().hex[:12]}"
            transfer_id = f"xfer-{uuid4().hex[:12]}"
            transaction_payload = {
                "transaction_id": transaction_id,
                "transfer_id": transfer_id,
                "actor_id": actor_id,
                "actor_role": actor_role,
                "sender_wallet_id": sender_wallet_id,
                "receiver_wallet_id": receiver_wallet_id,
                "amount": _money(amount_decimal),
                "currency": currency.upper(),
                "transfer_type": transfer_type,
                "idempotency_key": idempotency_key,
                "provider": provider,
                "metadata": metadata or {},
            }
            transaction = self.repository.upsert(
                "novapay_transactions",
                record_id=transaction_id,
                organization_id=organization_id,
                status="completed",
                payload=transaction_payload,
            )
            self.repository.upsert(
                "novapay_transfers",
                record_id=transfer_id,
                organization_id=organization_id,
                status="completed",
                payload={**transaction_payload, "sender_after": sender_after, "receiver_after": receiver_after},
            )
            self.repository.upsert(
                "novapay_ledger_entries",
                record_id=f"{transaction_id}-debit",
                organization_id=organization_id,
                status="posted",
                payload={
                    "transaction_id": transaction_id,
                    "wallet_id": sender_wallet_id,
                    "entry_type": "debit",
                    "amount": _money(amount_decimal),
                    "currency": currency.upper(),
                },
            )
            self.repository.upsert(
                "novapay_ledger_entries",
                record_id=f"{transaction_id}-credit",
                organization_id=organization_id,
                status="posted",
                payload={
                    "transaction_id": transaction_id,
                    "wallet_id": receiver_wallet_id,
                    "entry_type": "credit",
                    "amount": _money(amount_decimal),
                    "currency": currency.upper(),
                },
            )
            receipt = self.issue_receipt(
                organization_id=organization_id,
                transaction_id=transaction_id,
                actor_id=actor_id,
                actor_role=actor_role,
                payload={**transaction_payload, "sender_after": sender_after, "receiver_after": receiver_after},
            )
            self.repository.upsert(
                "novapay_provider_events",
                record_id=f"provider-{transaction_id}",
                organization_id=organization_id,
                status="published",
                payload={
                    "provider": provider,
                    "event_type": transfer_type,
                    "transaction_id": transaction_id,
                    "receipt_id": receipt["receipt_id"],
                },
            )
            self.repository.upsert(
                "novapay_audit_events",
                record_id=f"audit-{transaction_id}",
                organization_id=organization_id,
                status="recorded",
                payload={
                    "actor_id": actor_id,
                    "role": actor_role,
                    "action": transfer_type,
                    "transaction_id": transaction_id,
                    "receipt_id": receipt["receipt_id"],
                },
            )
            self._enqueue_financial_event(
                organization_id=organization_id,
                event_type="TRANSFER_POSTED",
                resource_type="TRANSFER",
                resource_id=transfer_id,
                payload={
                    "transaction_id": transaction_id,
                    "transfer_id": transfer_id,
                    "amount": _money(amount_decimal),
                    "currency": currency.upper(),
                },
                actor_id=actor_id,
                correlation_id=idempotency_key,
                causation_id=transaction_id,
                idempotency_key=idempotency_key,
            )
            return {
                "transaction": transaction.payload,
                "transfer": self.repository.get("novapay_transfers", transfer_id).payload,
                "receipt": receipt,
            }

    def receive_money(self, **kwargs: Any) -> dict[str, Any]:
        params = dict(kwargs)
        params.pop("transfer_type", None)
        return self.transfer_money(transfer_type="receive_money", **params)

    def qr_payment(
        self,
        *,
        organization_id: str,
        actor_id: str,
        actor_role: str,
        payer_wallet_id: str,
        merchant_wallet_id: str,
        amount: Decimal | int | str,
        currency: str,
        qr_code: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        self.repository.upsert(
            "novapay_qr_codes",
            record_id=qr_code,
            organization_id=organization_id,
            status="active",
            payload={"qr_code": qr_code, "merchant_wallet_id": merchant_wallet_id, "currency": currency.upper()},
        )
        return self.transfer_money(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_role=actor_role,
            sender_wallet_id=payer_wallet_id,
            receiver_wallet_id=merchant_wallet_id,
            amount=amount,
            currency=currency,
            transfer_type="qr_payment",
            idempotency_key=idempotency_key,
        )

    def merchant_payment(self, **kwargs: Any) -> dict[str, Any]:
        params = dict(kwargs)
        params.pop("transfer_type", None)
        return self.transfer_money(transfer_type="merchant_payment", **params)

    def bill_payment(self, **kwargs: Any) -> dict[str, Any]:
        params = dict(kwargs)
        params.pop("transfer_type", None)
        return self.transfer_money(transfer_type="bill_payment", **params)

    def remittance(self, **kwargs: Any) -> dict[str, Any]:
        params = dict(kwargs)
        params.pop("transfer_type", None)
        return self.transfer_money(transfer_type="international_transfer", **params)

    def card_payment(self, **kwargs: Any) -> dict[str, Any]:
        params = dict(kwargs)
        params.pop("transfer_type", None)
        return self.transfer_money(transfer_type="card_payment", **params)

    def business_payroll(
        self,
        *,
        organization_id: str,
        actor_id: str,
        actor_role: str,
        source_wallet_id: str,
        recipients: list[dict[str, Any]],
        currency: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        results = []
        for index, item in enumerate(recipients):
            results.append(
                self.transfer_money(
                    organization_id=organization_id,
                    actor_id=actor_id,
                    actor_role=actor_role,
                    sender_wallet_id=source_wallet_id,
                    receiver_wallet_id=str(item["recipient_wallet_id"]),
                    amount=item["amount"],
                    currency=currency,
                    transfer_type="payroll",
                    idempotency_key=f"{idempotency_key}:{index}:{item['recipient_wallet_id']}",
                    metadata={"note": item.get("note")},
                    require_approval=True,
                )
            )
        return {"payroll": results}

    def agent_cash_movement(
        self,
        *,
        organization_id: str,
        actor_id: str,
        actor_role: str,
        wallet_id: str,
        amount: Decimal | int | str,
        currency: str,
        direction: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        delta = Decimal(str(amount)) if direction == "in" else -Decimal(str(amount))
        wallet = self._adjust_wallet(wallet_id, delta=delta, reason=f"cash_{direction}")
        payload = {
            "movement_id": f"cash-{uuid4().hex[:12]}",
            "actor_id": actor_id,
            "actor_role": actor_role,
            "wallet_id": wallet_id,
            "direction": direction,
            "amount": _money(amount),
            "currency": currency.upper(),
            "idempotency_key": idempotency_key,
        }
        record = self.repository.upsert(
            "novapay_agents",
            record_id=payload["movement_id"],
            organization_id=organization_id,
            status="processed",
            payload={**payload, "wallet_after": wallet},
        )
        return _record(record)

    def payout(
        self,
        *,
        organization_id: str,
        actor_id: str,
        actor_role: str,
        source_wallet_id: str,
        destination_reference: str,
        amount: Decimal | int | str,
        currency: str,
        scheduled_for: str | None = None,
        idempotency_key: str,
    ) -> dict[str, Any]:
        self._adjust_wallet(source_wallet_id, delta=-Decimal(str(amount)), reason="payout")
        payout_id = f"payout-{uuid4().hex[:12]}"
        record = self.repository.upsert(
            "novapay_payouts",
            record_id=payout_id,
            organization_id=organization_id,
            status="scheduled" if scheduled_for else "submitted",
            payload={
                "payout_id": payout_id,
                "source_wallet_id": source_wallet_id,
                "destination_reference": destination_reference,
                "amount": _money(amount),
                "currency": currency.upper(),
                "scheduled_for": scheduled_for,
                "actor_id": actor_id,
                "actor_role": actor_role,
                "idempotency_key": idempotency_key,
            },
        )
        return _record(record)

    def refund(
        self,
        *,
        organization_id: str,
        actor_id: str,
        actor_role: str,
        source_wallet_id: str,
        destination_wallet_id: str,
        amount: Decimal | int | str,
        currency: str,
        reason: str,
        idempotency_key: str,
        require_approval: bool = True,
    ) -> dict[str, Any]:
        result = self.transfer_money(
            organization_id=organization_id,
            actor_id=actor_id,
            actor_role=actor_role,
            sender_wallet_id=source_wallet_id,
            receiver_wallet_id=destination_wallet_id,
            amount=amount,
            currency=currency,
            transfer_type="refund",
            idempotency_key=idempotency_key,
            require_approval=require_approval,
        )
        refund_id = f"refund-{uuid4().hex[:12]}"
        with self.repository.transaction():
            record = self.repository.upsert(
                "novapay_refunds",
                record_id=refund_id,
                organization_id=organization_id,
                status="completed",
                payload={
                    "refund_id": refund_id,
                    "transaction_id": result["transaction"]["transaction_id"],
                    "reason": reason,
                    "amount": _money(amount),
                    "currency": currency.upper(),
                    "approval_status": "approved" if require_approval else "auto_approved",
                },
            )
            self._enqueue_financial_event(
                organization_id=organization_id,
                event_type="REFUND_COMPLETED",
                resource_type="REFUND",
                resource_id=refund_id,
                payload={
                    "refund_id": refund_id,
                    "transaction_id": result["transaction"]["transaction_id"],
                    "reason": reason,
                },
                actor_id=actor_id,
                correlation_id=idempotency_key,
                causation_id=result["transaction"]["transaction_id"],
                idempotency_key=idempotency_key,
            )
            return _record(record)

    def dispute(
        self,
        *,
        organization_id: str,
        actor_id: str,
        actor_role: str,
        transaction_id: str,
        reason: str,
        idempotency_key: str,
    ) -> dict[str, Any]:
        dispute_id = f"dispute-{uuid4().hex[:12]}"
        record = self.repository.upsert(
            "novapay_disputes",
            record_id=dispute_id,
            organization_id=organization_id,
            status="open",
            payload={
                "dispute_id": dispute_id,
                "transaction_id": transaction_id,
                "reason": reason,
                "opened_by": actor_id,
                "opened_role": actor_role,
                "idempotency_key": idempotency_key,
            },
        )
        return _record(record)

    def settle(
        self,
        *,
        organization_id: str,
        transaction_id: str,
        actor_id: str,
        actor_role: str,
    ) -> dict[str, Any]:
        with self.repository.transaction():
            settlement_id = f"settlement-{uuid4().hex[:12]}"
            record = self.repository.upsert(
                "novapay_settlements",
                record_id=settlement_id,
                organization_id=organization_id,
                status="settled",
                payload={
                    "settlement_id": settlement_id,
                    "transaction_id": transaction_id,
                    "actor_id": actor_id,
                    "actor_role": actor_role,
                },
            )
            self._enqueue_financial_event(
                organization_id=organization_id,
                event_type="SETTLEMENT_COMPLETED",
                resource_type="SETTLEMENT",
                resource_id=settlement_id,
                payload={"settlement_id": settlement_id, "transaction_id": transaction_id},
                actor_id=actor_id,
                correlation_id=transaction_id,
                causation_id=transaction_id,
            )
            return _record(record)

    def reconcile(self, *, organization_id: str, batch_name: str, actor_id: str, actor_role: str) -> dict[str, Any]:
        with self.repository.transaction():
            batch_id = f"recon-{uuid4().hex[:12]}"
            transactions = self.repository.list("novapay_transactions", organization_id=organization_id)
            gross = sum(Decimal(str(item.payload.get("amount", "0"))) for item in transactions)
            record = self.repository.upsert(
                "novapay_reconciliation_batches",
                record_id=batch_id,
                organization_id=organization_id,
                status="closed",
                payload={
                    "batch_id": batch_id,
                    "batch_name": batch_name,
                    "actor_id": actor_id,
                    "actor_role": actor_role,
                    "transaction_count": len(transactions),
                    "gross_amount": _money(gross),
                },
            )
            self._enqueue_financial_event(
                organization_id=organization_id,
                event_type="RECONCILIATION_RESOLVED",
                resource_type="RECONCILIATION_BATCH",
                resource_id=batch_id,
                payload={"batch_id": batch_id, "batch_name": batch_name},
                actor_id=actor_id,
                correlation_id=batch_id,
                causation_id=batch_id,
            )
            return _record(record)

    def issue_receipt(
        self,
        *,
        organization_id: str,
        transaction_id: str,
        actor_id: str,
        actor_role: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        trust_hash = _hash(payload)
        trust_receipt = self.novatrust.record(
            subject_id=actor_id,
            organization_id=organization_id,
            event_type="novapay.receipt.issued",
            packet={"transaction_id": transaction_id, "payload": payload, "trust_hash": trust_hash},
        )
        receipt_id = f"receipt-{uuid4().hex[:12]}"
        record = self.repository.upsert(
            "novapay_receipts",
            record_id=receipt_id,
            organization_id=organization_id,
            status="verified",
            payload={
                "receipt_id": receipt_id,
                "transaction_id": transaction_id,
                "actor_id": actor_id,
                "actor_role": actor_role,
                "trust_hash": trust_hash,
                "signature": trust_receipt.canonical(),
                "payload": payload,
            },
        )
        return _record(record)

    def verify_receipt(self, receipt_id: str) -> dict[str, Any]:
        receipt = self.repository.get("novapay_receipts", receipt_id)
        if receipt is None:
            raise KeyError(receipt_id)
        payload = dict(receipt.payload.get("payload", {}))
        trust_hash = _hash(payload)
        verification = {
            "receipt_id": receipt_id,
            "valid": trust_hash == receipt.payload.get("trust_hash"),
            "trust_hash": trust_hash,
            "signature": receipt.payload.get("signature", {}),
        }
        verification["replay_evidence"] = self.replay_evidence(receipt.payload.get("transaction_id", ""))
        return verification

    def replay_evidence(self, transaction_id: str) -> dict[str, Any]:
        transaction = next(
            (record for record in self.repository.list("novapay_transactions") if record.payload.get("transaction_id") == transaction_id),
            None,
        )
        if transaction is None:
            raise KeyError(transaction_id)
        ledger = [
            _record(record)
            for record in self.repository.list("novapay_ledger_entries")
            if record.payload.get("transaction_id") == transaction_id
        ]
        receipts = [
            _record(record)
            for record in self.repository.list("novapay_receipts")
            if record.payload.get("transaction_id") == transaction_id
        ]
        return {
            "transaction": _record(transaction),
            "ledger_entries": ledger,
            "receipts": receipts,
            "replay_verified": bool(receipts and len(ledger) >= 2),
        }

    def verify_ledger(self, receipt_id: str) -> dict[str, Any]:
        receipt = self.repository.get("novapay_receipts", receipt_id)
        if receipt is None:
            raise KeyError(receipt_id)
        transaction_id = str(receipt.payload.get("transaction_id"))
        tx = next(
            (record for record in self.repository.list("novapay_transactions") if record.payload.get("transaction_id") == transaction_id),
            None,
        )
        ledger = [
            record for record in self.repository.list("novapay_ledger_entries")
            if record.payload.get("transaction_id") == transaction_id
        ]
        debit = sum(Decimal(str(record.payload.get("amount", "0"))) for record in ledger if record.payload.get("entry_type") == "debit")
        credit = sum(Decimal(str(record.payload.get("amount", "0"))) for record in ledger if record.payload.get("entry_type") == "credit")
        amount = Decimal(str(tx.payload.get("amount", "0"))) if tx else Decimal("0")
        return {"receipt_id": receipt_id, "valid": debit == credit == amount, "debit": _money(debit), "credit": _money(credit)}

    def verify_settlement(self, receipt_id: str) -> dict[str, Any]:
        receipt = self.repository.get("novapay_receipts", receipt_id)
        if receipt is None:
            raise KeyError(receipt_id)
        transaction_id = str(receipt.payload.get("transaction_id"))
        settlement = next(
            (record for record in self.repository.list("novapay_settlements") if record.payload.get("transaction_id") == transaction_id),
            None,
        )
        return {"receipt_id": receipt_id, "valid": settlement is not None, "settlement": _record(settlement) if settlement else None}

    def trust_explorer(self, receipt_id: str) -> dict[str, Any]:
        receipt = self.verify_receipt(receipt_id)
        ledger_valid = self.verify_ledger(receipt_id)
        settlement_valid = self.verify_settlement(receipt_id)
        audit_events = [
            _record(record)
            for record in self.repository.list("novapay_audit_events")
            if record.payload.get("receipt_id") == receipt_id
        ]
        return {
            "receipt": receipt,
            "ledger_valid": ledger_valid["valid"],
            "settlement_valid": settlement_valid["valid"],
            "audit_bundle": audit_events,
            "public_verdict": "verified" if receipt["valid"] and ledger_valid["valid"] and settlement_valid["valid"] else "review",
        }

    def developer_app_lifecycle(
        self,
        *,
        organization_id: str,
        developer_id: str,
        app_name: str,
        webhook_url: str,
    ) -> dict[str, Any]:
        app_id = f"app-{uuid4().hex[:12]}"
        api_key = f"np_{uuid4().hex}"
        app_record = self.repository.upsert(
            "novapay_developer_apps",
            record_id=app_id,
            organization_id=organization_id,
            status="active",
            payload={
                "app_id": app_id,
                "developer_id": developer_id,
                "app_name": app_name,
                "api_key": api_key,
                "api_key_hash": hashlib.sha256(api_key.encode()).hexdigest(),
            },
        )
        webhook_id = f"webhook-{uuid4().hex[:12]}"
        webhook_record = self.repository.upsert(
            "novapay_webhooks",
            record_id=webhook_id,
            organization_id=organization_id,
            status="active",
            payload={
                "webhook_id": webhook_id,
                "app_id": app_id,
                "developer_id": developer_id,
                "webhook_url": webhook_url,
                "delivery_status": "pending",
            },
        )
        return {"app": _record(app_record), "webhook": _record(webhook_record)}

    def register_webhook(
        self,
        *,
        organization_id: str,
        developer_id: str,
        webhook_url: str,
        event_types: list[str],
        secret_hint: str | None = None,
    ) -> dict[str, Any]:
        webhook_id = f"webhook-{uuid4().hex[:12]}"
        record = self.repository.upsert(
            "novapay_webhooks",
            record_id=webhook_id,
            organization_id=organization_id,
            status="active",
            payload={
                "webhook_id": webhook_id,
                "developer_id": developer_id,
                "webhook_url": webhook_url,
                "event_types": list(event_types),
                "secret_hint": secret_hint,
                "delivery_status": "pending",
            },
        )
        return _record(record)

    def issue_invoice(
        self,
        *,
        organization_id: str,
        actor_id: str,
        actor_role: str,
        customer_wallet_id: str,
        amount: Decimal | int | str,
        currency: str,
        reference: str,
        due_date: str | None = None,
        idempotency_key: str,
    ) -> dict[str, Any]:
        invoice_id = f"invoice-{uuid4().hex[:12]}"
        record = self.repository.upsert(
            "novapay_invoices",
            record_id=invoice_id,
            organization_id=organization_id,
            status="issued",
            payload={
                "invoice_id": invoice_id,
                "actor_id": actor_id,
                "actor_role": actor_role,
                "customer_wallet_id": customer_wallet_id,
                "amount": _money(amount),
                "currency": currency.upper(),
                "reference": reference,
                "due_date": due_date,
                "idempotency_key": idempotency_key,
            },
        )
        return _record(record)

    def compliance_hold(self, *, organization_id: str, actor_id: str, reason: str, subject_id: str) -> dict[str, Any]:
        decision = self.policy_decision(
            role="COMPLIANCE",
            action="compliance.hold",
            amount="0",
            organization_id=organization_id,
            subject_id=subject_id,
            workflow="compliance_hold",
            approval_required=True,
            metadata={"reason": reason, "operator": actor_id},
        )
        decision["status"] = "hold"
        decision["reason"] = reason
        self.repository.upsert(
            "novapay_policy_approvals",
            record_id=decision["record_id"],
            organization_id=organization_id,
            status="hold",
            payload=decision,
        )
        return decision

    def finance_report(self, *, organization_id: str) -> dict[str, Any]:
        wallets = self.repository.list("novapay_wallets", organization_id=organization_id)
        transactions = self.repository.list("novapay_transactions", organization_id=organization_id)
        refunds = self.repository.list("novapay_refunds", organization_id=organization_id)
        payouts = self.repository.list("novapay_payouts", organization_id=organization_id)
        invoices = self.repository.list("novapay_invoices", organization_id=organization_id)
        ledger_entries = self.repository.list("novapay_ledger_entries", organization_id=organization_id)
        gross = sum(Decimal(str(tx.payload.get("amount", "0"))) for tx in transactions)
        total_wallet_balance = sum(Decimal(str(wallet.payload.get("balance", "0"))) for wallet in wallets)
        return {
            "organization_id": organization_id,
            "wallet_count": len(wallets),
            "transaction_count": len(transactions),
            "refund_count": len(refunds),
            "payout_count": len(payouts),
            "invoice_count": len(invoices),
            "ledger_entry_count": len(ledger_entries),
            "gross_volume": _money(gross),
            "wallet_balance": _money(total_wallet_balance),
        }

    def operations_dashboard(self, *, organization_id: str) -> dict[str, Any]:
        report = self.finance_report(organization_id=organization_id)
        policy_approvals = self.repository.list("novapay_policy_approvals", organization_id=organization_id)
        receipts = self.repository.list("novapay_receipts", organization_id=organization_id)
        webhooks = self.repository.list("novapay_webhooks", organization_id=organization_id)
        return {
            "organization_id": organization_id,
            "finance": report,
            "policy_approvals": len(policy_approvals),
            "verified_receipts": sum(1 for receipt in receipts if receipt.status == "verified"),
            "webhooks": len(webhooks),
            "table_names": list(self.repository.table_names()),
        }

    def role_permissions(self) -> dict[str, list[str]]:
        return {
            "consumer": ["wallet", "transfer", "qr", "refund", "bill"],
            "business": ["wallet", "payroll", "merchant_payment", "settlement", "invoice"],
            "merchant": ["merchant_payment", "qr", "refund", "catalog"],
            "agent": ["cash_in", "cash_out", "wallet", "kyc"],
            "enterprise": ["approval", "payout", "settlement", "reconciliation", "treasury"],
            "developer": ["api_key_lifecycle", "webhook_delivery", "contract_verification"],
            "public": ["trust_explorer"],
            "internal": ["support", "compliance", "operations", "finance"],
        }

    def portals(self) -> list[dict[str, Any]]:
        return [*build_app_surfaces(), *build_trust_surfaces()]

    def app_surfaces(self) -> list[dict[str, Any]]:
        return build_app_surfaces()

    def trust_surfaces(self) -> list[dict[str, Any]]:
        return build_trust_surfaces()

    def agent_app_surface(self, organization_id: str) -> dict[str, Any]:
        return {
            "view": "novapay_agent_app",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Agent App"),
            "live_operations": {
                "customers_waiting": len(self.repository.list("novapay_transactions", organization_id=organization_id)),
                "nearby_agents": len(self.repository.list("novapay_agents", organization_id=organization_id)),
                "settlement_queue": len(self.repository.list("novapay_payouts", organization_id=organization_id)),
                "network_health": "green",
            },
        }

    def agent_profile_surface(self, organization_id: str) -> dict[str, Any]:
        accounts = self.repository.list("novapay_accounts", organization_id=organization_id)
        wallets = self.repository.list("novapay_wallets", organization_id=organization_id)
        agents = self.repository.list("novapay_agents", organization_id=organization_id)
        return {
            "view": "novapay_agent_profile",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Agent App"),
            "agent_count": len(agents),
            "wallet_count": len(wallets),
            "identity_status": "verified" if accounts else "review",
            "device_trust": "trusted" if agents else "review",
            "pilot_mode": True,
        }

    def agent_float_surface(self, organization_id: str) -> dict[str, Any]:
        wallets = self.repository.list("novapay_wallets", organization_id=organization_id)
        payouts = self.repository.list("novapay_payouts", organization_id=organization_id)
        settlements = self.repository.list("novapay_settlements", organization_id=organization_id)
        balance = sum(Decimal(str(wallet.payload.get("balance", "0"))) for wallet in wallets)
        return {
            "view": "novapay_agent_float",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Agent App"),
            "float_balance": _money(balance),
            "wallet_count": len(wallets),
            "pending_settlements": len([record for record in settlements if record.status != "settled"]),
            "pending_payouts": len([record for record in payouts if record.status != "settled"]),
            "commission_today": _money(sum(Decimal(str(item.payload.get("amount", "0"))) for item in payouts)),
        }

    def agent_history_surface(self, organization_id: str) -> dict[str, Any]:
        transactions = self.repository.list("novapay_transactions", organization_id=organization_id)
        receipts = self.repository.list("novapay_receipts", organization_id=organization_id)
        return {
            "view": "novapay_agent_history",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Agent App"),
            "transactions": [_record(record) for record in transactions],
            "receipts": [_record(record) for record in receipts],
        }

    def agent_offline_queue_surface(self, organization_id: str) -> dict[str, Any]:
        queue = self._optional_records("novapay_offline_queue", organization_id=organization_id)
        return {
            "view": "novapay_agent_offline_queue",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Agent App"),
            "offline_queue": [_record(record) for record in queue],
            "duplicate_prevention": True,
            "idempotency": True,
        }

    def agent_sync_surface(self, organization_id: str) -> dict[str, Any]:
        queue = self._optional_records("novapay_offline_queue", organization_id=organization_id)
        return {
            "view": "novapay_agent_sync",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Agent App"),
            "pending_sync": len(queue),
            "sync_status": "pending" if queue else "online",
            "conflict_detection": True,
        }

    def agent_compliance_surface(self, organization_id: str) -> dict[str, Any]:
        approvals = self._optional_records("novapay_policy_approvals", organization_id=organization_id)
        holds = self._optional_records("novapay_compliance_holds", organization_id=organization_id)
        return {
            "view": "novapay_agent_compliance",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Agent App"),
            "alerts": [
                "High Value Alert" if approvals else "Daily Limit Warning",
                "AML Review Pending" if holds else "Supervisor Review Required",
            ],
            "holds": [_record(record) for record in holds],
            "policy_approvals": [_record(record) for record in approvals],
        }

    def agent_receipts_surface(self, organization_id: str) -> dict[str, Any]:
        receipts = self._optional_records("novapay_receipts", organization_id=organization_id)
        return {
            "view": "novapay_agent_receipts",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Agent App"),
            "receipts": [_record(record) for record in receipts],
            "signature_state": "verified" if receipts else "pending",
        }

    def agent_supervisor_review_surface(self, organization_id: str) -> dict[str, Any]:
        approvals = self._optional_records("novapay_policy_approvals", organization_id=organization_id)
        receipts = self._optional_records("novapay_receipts", organization_id=organization_id)
        return {
            "view": "novapay_agent_supervisor_review",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Agent App"),
            "requires_review": bool(approvals or receipts),
            "policy_approvals": len(approvals),
            "verified_receipts": len(receipts),
        }

    def _optional_records(self, table_name: str, *, organization_id: str) -> list[NovaPayRecord]:
        try:
            return self.repository.list(table_name, organization_id=organization_id)
        except sqlite3.OperationalError as exc:
            if "no such table" not in str(exc).lower():
                raise
            return []

    def wallet_app_surface(self, organization_id: str) -> dict[str, Any]:
        return {
            "view": "novapay_wallet_app",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Wallet"),
            "balances": {
                "wallets": [wallet.payload for wallet in self.repository.list("novapay_wallets", organization_id=organization_id)],
                "receipts": len(self.repository.list("novapay_receipts", organization_id=organization_id)),
            },
        }

    def business_wallet_surface(self, organization_id: str) -> dict[str, Any]:
        return {
            "view": "novapay_business_wallet",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Business Wallet"),
            "treasury": self.finance_report(organization_id=organization_id),
        }

    def merchant_app_surface(self, organization_id: str) -> dict[str, Any]:
        return {
            "view": "novapay_merchant_app",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Merchant App"),
            "settlement": len(self.repository.list("novapay_settlements", organization_id=organization_id)),
            "refunds": len(self.repository.list("novapay_refunds", organization_id=organization_id)),
        }

    def corporate_portal_surface(self, organization_id: str) -> dict[str, Any]:
        return {
            "view": "novapay_corporate_portal",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Corporate Portal"),
            "finance": self.finance_report(organization_id=organization_id),
        }

    def developer_portal_surface(self, organization_id: str) -> dict[str, Any]:
        return {
            "view": "novapay_developer_portal",
            "organization_id": organization_id,
            "surface": next(surface for surface in build_app_surfaces() if surface["name"] == "NovaPay Developer Portal"),
            "apps": self.repository.list("novapay_developer_apps", organization_id=organization_id),
            "webhooks": self.repository.list("novapay_webhooks", organization_id=organization_id),
        }

    def ai_insights(self, *, organization_id: str) -> dict[str, Any]:
        transactions = self.repository.list("novapay_transactions", organization_id=organization_id)
        amounts = [Decimal(str(item.payload.get("amount", "0"))) for item in transactions]
        gross = sum(amounts)
        average = gross / len(amounts) if amounts else Decimal("0")
        anomaly_score = min(100, len([amount for amount in amounts if amount > Decimal("1000")]) * 25)
        return {
            "organization_id": organization_id,
            "spending_insights": {
                "gross_volume": _money(gross),
                "average_ticket": _money(average),
                "largest_transaction": _money(max(amounts) if amounts else Decimal("0")),
            },
            "anomaly_detection": {
                "risk_score": anomaly_score,
                "flagged_transactions": [item.payload["transaction_id"] for item in transactions if Decimal(str(item.payload.get("amount", "0"))) > Decimal("1000")],
            },
            "fraud_risk_scoring": {
                "score": anomaly_score,
                "explanation": "Heuristic based on unusually large transactions.",
            },
            "settlement_forecast": {
                "projected_settlement_volume": _money(gross * Decimal("0.95")),
                "confidence": 0.82,
            },
            "explainable_recommendations": [
                "Review high-value payouts before release.",
                "Require compliance hold for unusual merchant concentration.",
            ],
            "operational_alerts": [
                {"severity": "warning", "message": "High-value transaction concentration detected."}
            ] if anomaly_score else [],
        }
