"""Persistent AfriPay stores shared across runtime layers."""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import json
import time
from importlib import import_module
from typing import Any

from django.db import IntegrityError, OperationalError, close_old_connections, transaction
from django.db.models import F
from django.utils import timezone
from datetime import timedelta


class PersistentIdempotencyStore:
    def claim(
        self,
        key: str,
        request_payload: dict[str, Any],
        ttl_seconds: int = 86400,
    ) -> tuple[Any, bool]:
        request_hash = _payload_hash(request_payload)
        idempotency_model = _afripay_models().IdempotencyKey
        for attempt in range(12):
            try:
                with transaction.atomic():
                    existing = idempotency_model.objects.select_for_update().filter(key=key).first()
                    if existing is not None:
                        if existing.expires_at is not None and existing.expires_at < timezone.now():
                            existing.delete()
                        else:
                            if existing.request_hash != request_hash:
                                raise ValueError("idempotency key reused with different request payload")
                            return existing, False
                    expires_at = timezone.now() + timedelta(seconds=ttl_seconds)
                    try:
                        with transaction.atomic():
                            item = idempotency_model.objects.create(
                                key=key,
                                request_hash=request_hash,
                                response={},
                                expires_at=expires_at,
                            )
                    except IntegrityError:
                        existing = idempotency_model.objects.select_for_update().filter(key=key).first()
                        if existing is None:
                            raise
                        if existing.expires_at is not None and existing.expires_at < timezone.now():
                            existing.delete()
                            with transaction.atomic():
                                item = idempotency_model.objects.create(
                                    key=key,
                                    request_hash=request_hash,
                                    response={},
                                    expires_at=expires_at,
                                )
                            return item, True
                        if existing.request_hash != request_hash:
                            raise ValueError("idempotency key reused with different request payload")
                        return existing, False
                    return item, True
            except OperationalError:
                if attempt >= 11:
                    raise
                close_old_connections()
                time.sleep(0.05 * (attempt + 1))
        raise OperationalError("idempotency claim exhausted retries")

    def get_existing_response(self, key: str) -> dict[str, Any] | None:
        idempotency_model = _afripay_models().IdempotencyKey
        item = idempotency_model.objects.filter(key=key, status="completed").first()
        if item is None:
            return None
        if item.expires_at is not None and item.expires_at < timezone.now():
            return None
        return dict(item.response)

    def prune_expired(self) -> int:
        idempotency_model = _afripay_models().IdempotencyKey
        deleted, _ = idempotency_model.objects.filter(expires_at__lt=timezone.now()).delete()
        return deleted

    def store_response(self, key: str, response: dict[str, Any]) -> None:
        with transaction.atomic():
            idempotency_model = _afripay_models().IdempotencyKey
            item = idempotency_model.objects.select_for_update().get(key=key)
            item.response = response
            item.status = "completed"
            item.save(update_fields=["response", "status", "updated_at"])


class PersistentTreasuryStore:
    def reserve(self, provider: str, currency: str, amount: Decimal) -> LiquidityPool:
        return _with_retry(lambda: self._reserve(provider, currency, amount))

    def settle(self, provider: str, currency: str, amount: Decimal) -> LiquidityPool:
        return _with_retry(lambda: self._settle(provider, currency, amount))

    def release(self, provider: str, currency: str, amount: Decimal) -> LiquidityPool:
        return _with_retry(lambda: self._release(provider, currency, amount))

    def _reserve(self, provider: str, currency: str, amount: Decimal) -> LiquidityPool:
        with transaction.atomic():
            liquidity_model = _afripay_models().LiquidityPool
            pool = (
                liquidity_model.objects.select_for_update(nowait=True)
                .get(provider=provider, currency=currency.upper())
            )
            if pool.balance - pool.reserved < amount:
                raise ValueError("insufficient provider liquidity")
            pool.reserved = F("reserved") + amount
            pool.save(update_fields=["reserved", "updated_at"])
            pool.refresh_from_db()
            return pool

    def _settle(self, provider: str, currency: str, amount: Decimal) -> LiquidityPool:
        with transaction.atomic():
            liquidity_model = _afripay_models().LiquidityPool
            pool = (
                liquidity_model.objects.select_for_update(nowait=True)
                .get(provider=provider, currency=currency.upper())
            )
            if pool.reserved < amount or pool.balance < amount:
                raise ValueError("invalid treasury settlement")
            pool.reserved = F("reserved") - amount
            pool.balance = F("balance") - amount
            pool.save(update_fields=["reserved", "balance", "updated_at"])
            pool.refresh_from_db()
            return pool

    def _release(self, provider: str, currency: str, amount: Decimal) -> LiquidityPool:
        with transaction.atomic():
            liquidity_model = _afripay_models().LiquidityPool
            pool = (
                liquidity_model.objects.select_for_update(nowait=True)
                .get(provider=provider, currency=currency.upper())
            )
            if pool.reserved < amount:
                raise ValueError("invalid treasury release")
            pool.reserved = F("reserved") - amount
            pool.save(update_fields=["reserved", "updated_at"])
            pool.refresh_from_db()
            return pool


def _payload_hash(payload: dict[str, Any]) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _with_retry(operation, *, attempts: int = 40, base_delay: float = 0.02):
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return operation()
        except (IntegrityError, OperationalError) as exc:
            last_error = exc
            if attempt + 1 >= attempts:
                raise
            close_old_connections()
            time.sleep(base_delay * (attempt + 1))
    if last_error is not None:
        raise last_error


def _afripay_models():
    return import_module("afriride_system.django_app.apps.afripay.models")
