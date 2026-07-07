"""Provider-neutral ride payments, wallets, payouts, refunds and disputes."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

from afriride_system.backend.storage import AfriRideStorage, decode_json_value
from afriride_system.payments.private_development import (
    guard_payment_boundary,
    mark_simulated_payment,
)


class PaymentProvider(Protocol):
    name: str
    def charge(self, transaction_id: str, amount_minor: int, currency: str) -> str: ...
    def refund(self, provider_reference: str, amount_minor: int, currency: str) -> str: ...
    def payout(self, payout_id: str, amount_minor: int, currency: str) -> str: ...


@dataclass
class ReferenceProvider:
    name: str
    live: bool = False

    def charge(self, transaction_id: str, amount_minor: int, currency: str) -> str:
        return f"{self.name}:charge:{transaction_id}"
    def refund(self, provider_reference: str, amount_minor: int, currency: str) -> str:
        return f"{self.name}:refund:{provider_reference}"
    def payout(self, payout_id: str, amount_minor: int, currency: str) -> str:
        return f"{self.name}:payout:{payout_id}"


class PaymentRepository:
    def __init__(self, storage: AfriRideStorage) -> None:
        self.storage = storage

    def wallet(self, owner_id: str, owner_type: str, currency: str) -> dict[str, Any]:
        currency = currency.upper()
        with self.storage.connect() as connection:
            row = connection.execute(
                "SELECT * FROM payment_wallets WHERE owner_id=? AND owner_type=? AND currency=?",
                (owner_id, owner_type, currency),
            ).fetchone()
            if not row:
                wallet_id = f"wallet-{uuid4().hex}"
                connection.execute(
                    "INSERT INTO payment_wallets VALUES (?, ?, ?, ?, ?)",
                    (wallet_id, owner_id, owner_type, currency, _now()),
                )
                row = {"wallet_id": wallet_id, "owner_id": owner_id,
                       "owner_type": owner_type, "currency": currency}
        return {**row, "balance_minor": self.balance(str(row["wallet_id"]))}

    def balance(self, wallet_id: str) -> int:
        with self.storage.connect() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(amount_minor), 0) AS balance FROM payment_ledger WHERE wallet_id=?",
                (wallet_id,),
            ).fetchone()
        return int(row["balance"])

    def post(self, wallet_id: str, amount_minor: int, entry_type: str, reference: str) -> None:
        with self.storage.connect() as connection:
            existing = connection.execute(
                "SELECT entry_id FROM payment_ledger WHERE wallet_id=? AND reference=? AND entry_type=?",
                (wallet_id, reference, entry_type),
            ).fetchone()
            if not existing:
                connection.execute(
                    "INSERT INTO payment_ledger VALUES (?, ?, ?, ?, ?, ?)",
                    (f"entry-{uuid4().hex}", wallet_id, amount_minor, entry_type, reference, _now()),
                )

    def transaction(self, transaction_id: str) -> dict[str, Any] | None:
        with self.storage.connect() as connection:
            row = connection.execute(
                "SELECT * FROM payment_transactions WHERE transaction_id=?", (transaction_id,)
            ).fetchone()
        return None if not row else {**row, "split": decode_json_value(row["split_json"])}

    def transaction_by_key(self, key: str) -> dict[str, Any] | None:
        with self.storage.connect() as connection:
            row = connection.execute(
                "SELECT * FROM payment_transactions WHERE idempotency_key=?", (key,)
            ).fetchone()
        return None if not row else {**row, "split": decode_json_value(row["split_json"])}

    def save_transaction(self, row: dict[str, Any]) -> None:
        with self.storage.connect() as connection:
            connection.execute(
                """INSERT INTO payment_transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (row["transaction_id"], row["idempotency_key"], row.get("ride_id"), row["payer_id"],
                 row["amount_minor"], row["currency"], row["method"], row["provider"],
                 row.get("provider_reference"), row["status"], json.dumps(row["split"]),
                 row.get("promotion_code"), row["created_at"], row["updated_at"]),
            )

    def update_transaction(self, transaction_id: str, status: str, provider_reference: str) -> None:
        with self.storage.connect() as connection:
            connection.execute(
                "UPDATE payment_transactions SET status=?, provider_reference=?, updated_at=? WHERE transaction_id=?",
                (status, provider_reference, _now(), transaction_id),
            )

    def create_dispute(self, transaction_id: str, opened_by: str, reason: str) -> dict[str, Any]:
        dispute_id, now = f"dispute-{uuid4().hex}", _now()
        with self.storage.connect() as connection:
            connection.execute(
                "INSERT INTO payment_disputes VALUES (?, ?, ?, ?, 'open', NULL, ?, ?)",
                (dispute_id, transaction_id, opened_by, reason, now, now),
            )
        return {"dispute_id": dispute_id, "transaction_id": transaction_id,
                "opened_by": opened_by, "reason": reason, "status": "open"}

    def create_promotion(self, code: str, credit_minor: int, currency: str, uses: int) -> dict[str, Any]:
        with self.storage.connect() as connection:
            connection.execute(
                """INSERT INTO payment_promotions VALUES (?, ?, ?, ?, 1)
                   ON CONFLICT(code) DO UPDATE SET credit_minor=excluded.credit_minor,
                   currency=excluded.currency, remaining_uses=excluded.remaining_uses, active=1""",
                (code.upper(), credit_minor, currency.upper(), uses),
            )
        return {"code": code.upper(), "credit_minor": credit_minor,
                "currency": currency.upper(), "remaining_uses": uses}

    def consume_promotion(self, code: str | None, currency: str) -> int:
        if not code:
            return 0
        with self.storage.connect() as connection:
            row = connection.execute(
                """SELECT credit_minor, remaining_uses, active FROM payment_promotions
                   WHERE code=? AND currency=?""", (code.upper(), currency.upper())
            ).fetchone()
            if not row or not row["active"] or int(row["remaining_uses"]) <= 0:
                raise ValueError("promotion_unavailable")
            connection.execute(
                "UPDATE payment_promotions SET remaining_uses=remaining_uses-1 WHERE code=?",
                (code.upper(),),
            )
        return int(row["credit_minor"])

    def schedule_payout(self, driver_id: str, amount_minor: int, currency: str,
                        scheduled_for: str) -> dict[str, Any]:
        payout_id = f"payout-{uuid4().hex}"
        with self.storage.connect() as connection:
            connection.execute(
                "INSERT INTO payment_payouts VALUES (?, ?, ?, ?, ?, 'scheduled', NULL, ?)",
                (payout_id, driver_id, amount_minor, currency.upper(), scheduled_for, _now()),
            )
        return {"payout_id": payout_id, "driver_id": driver_id,
                "amount_minor": amount_minor, "currency": currency.upper(),
                "scheduled_for": scheduled_for, "status": "scheduled"}

    def report(self) -> dict[str, Any]:
        with self.storage.connect() as connection:
            rows = connection.execute(
                "SELECT split_json FROM payment_transactions WHERE status IN ('captured','partially_refunded')"
            ).fetchall()
        splits = [decode_json_value(row["split_json"]) for row in rows]
        return {
            "gross_minor": sum(sum(int(v) for v in split.values()) for split in splits),
            "driver_minor": sum(int(split["driver_minor"]) for split in splits),
            "commission_minor": sum(int(split["commission_minor"]) for split in splits),
            "tax_minor": sum(int(split["tax_minor"]) for split in splits),
            "promotion_minor": sum(int(split["promotion_minor"]) for split in splits),
        }

    def health(self) -> dict[str, Any]:
        with self.storage.connect() as connection:
            transactions = connection.execute(
                "SELECT status, COUNT(*) AS count FROM payment_transactions GROUP BY status"
            ).fetchall()
            disputes = connection.execute(
                "SELECT COUNT(*) AS count FROM payment_disputes WHERE status='open'"
            ).fetchone()
            payouts = connection.execute(
                "SELECT COUNT(*) AS count FROM payment_payouts WHERE status='scheduled'"
            ).fetchone()
        return {"transactions": {row["status"]: row["count"] for row in transactions},
                "open_disputes": disputes["count"], "scheduled_payouts": payouts["count"]}


class PaymentService:
    def __init__(self, repository: PaymentRepository, providers: dict[str, PaymentProvider]) -> None:
        self.repository, self.providers = repository, providers

    def charge(self, *, idempotency_key: str, payer_id: str, amount_minor: int,
               currency: str, method: str, provider: str, ride_id: str | None,
               driver_id: str | None, promotion_code: str | None = None) -> dict[str, Any]:
        existing = self.repository.transaction_by_key(idempotency_key)
        if existing:
            return existing
        if provider not in self.providers:
            raise ValueError("unsupported_payment_provider")
        guard_payment_boundary(provider=provider, method=method)
        discount = min(amount_minor, self.repository.consume_promotion(promotion_code, currency))
        net = amount_minor - discount
        commission, tax = round(net * 0.20), round(net * 0.10)
        driver_share = net - commission - tax
        split = {"driver_minor": driver_share, "commission_minor": commission,
                 "tax_minor": tax, "promotion_minor": discount}
        transaction_id, now = f"payment-{uuid4().hex}", _now()
        reference = self.providers[provider].charge(transaction_id, net, currency)
        row = {
            "transaction_id": transaction_id, "idempotency_key": idempotency_key,
            "ride_id": ride_id, "payer_id": payer_id, "amount_minor": net,
            "currency": currency.upper(), "method": method, "provider": provider,
            "provider_reference": reference, "status": "captured", "split": split,
            "promotion_code": promotion_code, "created_at": now, "updated_at": now,
            "simulated_payment": True,
        }
        self.repository.save_transaction(row)
        if driver_id:
            wallet = self.repository.wallet(driver_id, "driver", currency)
            self.repository.post(wallet["wallet_id"], driver_share, "ride_earning", transaction_id)
        return mark_simulated_payment(row)

    def refund(self, transaction_id: str, amount_minor: int) -> dict[str, Any]:
        tx = self.repository.transaction(transaction_id)
        if not tx or tx["status"] not in {"captured", "partially_refunded"}:
            raise ValueError("transaction_not_refundable")
        if amount_minor <= 0 or amount_minor > tx["amount_minor"]:
            raise ValueError("invalid_refund_amount")
        guard_payment_boundary(provider=str(tx["provider"]), method=str(tx["method"]))
        reference = self.providers[tx["provider"]].refund(
            tx["provider_reference"], amount_minor, tx["currency"]
        )
        status = "refunded" if amount_minor == tx["amount_minor"] else "partially_refunded"
        self.repository.update_transaction(transaction_id, status, reference)
        return mark_simulated_payment({"transaction_id": transaction_id, "refund_minor": amount_minor,
                "status": status, "provider_reference": reference})


def default_payment_service(storage: AfriRideStorage) -> PaymentService:
    providers = {
        "stripe": ReferenceProvider("stripe"),
        "flutterwave": ReferenceProvider("flutterwave"),
        "cash": ReferenceProvider("cash"),
        "wallet": ReferenceProvider("wallet"),
    }
    return PaymentService(PaymentRepository(storage), providers)


def _now() -> str:
    return datetime.now(UTC).isoformat()
