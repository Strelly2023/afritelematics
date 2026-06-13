"""Shared AfriPay operations used by runtime layers."""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import json
from importlib import import_module
from typing import Any

from django.db import transaction as db_transaction

from afritech.afripay.api import AfriPayService
from afritech.afripay.events import canonical_hash
from afritech.afripay.persistence import PersistentTreasuryStore


def create_payment_sync(data: dict[str, Any]) -> dict[str, Any]:
    service_response = AfriPayService().create_payment(
        {
            "payer_id": data["payer_id"],
            "payee_id": data["payee_id"],
            "amount": str(data["amount"]),
            "currency": data["currency"],
            "reference": data["reference"],
            "preference": data["preference"],
            "metadata": data.get("metadata", {}),
        }
    )
    treasury = PersistentTreasuryStore()
    with db_transaction.atomic():
        payer = party(data["payer_id"], data["payer_country"], data["payer_kyc_level"])
        payee = party(data["payee_id"], data["payee_country"], data["payee_kyc_level"])
        models = _afripay_models()
        tx = models.Transaction.objects.create(
            transaction_id=service_response["transaction_id"],
            reference=service_response["reference"],
            payer=payer,
            payee=payee,
            amount=data["amount"],
            currency=data["currency"].upper(),
            transaction_type="payment",
            status=service_response["status"],
            metadata=data.get("metadata", {}),
        )
        for route in service_response["routes"]:
            amount = Decimal(route["amount"]["amount"])
            route_reference = route.get("external_reference") or f"route.{canonical_hash(route)[:24]}"
            models.PaymentRoute.objects.create(
                route_id=route_reference,
                transaction=tx,
                provider=route["provider"],
                rail=route["rail"],
                amount=amount,
                currency=route["amount"]["currency"],
                fee=Decimal("0.00"),
                status=route["status"],
                external_reference=route_reference,
            )
            ensure_pool(route["provider"], route["amount"]["currency"])
            treasury.reserve(route["provider"], route["amount"]["currency"], amount)
            treasury.settle(route["provider"], route["amount"]["currency"], amount)
            models.ProviderTransaction.objects.create(
                provider=route["provider"],
                transaction=tx,
                internal_reference=tx.reference,
                external_reference=route_reference,
                status=route["status"],
                raw_response=route,
            )
        append_event("afripay.payment.completed", tx.reference, service_response)
    return service_response


def party(party_id: str, country: str, kyc_level: int):
    models = _afripay_models()
    party_obj, _ = models.AfriPayParty.objects.get_or_create(
        party_id=party_id,
        defaults={"country": country.upper(), "kyc_level": kyc_level},
    )
    return party_obj


def ensure_pool(provider: str, currency: str):
    models = _afripay_models()
    pool, _ = models.LiquidityPool.objects.get_or_create(
        provider=provider,
        currency=currency.upper(),
        defaults={
            "pool_id": f"pool.{provider}.{currency.lower()}",
            "balance": Decimal("1000000.00"),
            "reserved": Decimal("0.00"),
            "low_watermark": Decimal("100.00"),
        },
    )
    return pool


def append_event(event_type: str, aggregate_id: str, payload: dict[str, Any]):
    models = _afripay_models()
    previous = models.EventRecord.objects.order_by("-id").first()
    previous_hash = previous.hash_chain if previous is not None else "GENESIS"
    event_id = "evt." + canonical_hash({"event_type": event_type, "aggregate_id": aggregate_id, "payload": payload})[:24]
    hash_chain = sha256(
        json.dumps(
            {
                "event_id": event_id,
                "event_type": event_type,
                "aggregate_id": aggregate_id,
                "payload": payload,
                "previous_hash": previous_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    return models.EventRecord.objects.create(
        event_id=event_id,
        event_type=event_type,
        aggregate_id=aggregate_id,
        payload=payload,
        hash_chain=hash_chain,
    )


def _afripay_models():
    return import_module("afriride_system.django_app.apps.afripay.models")
