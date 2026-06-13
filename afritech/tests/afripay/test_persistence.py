from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from importlib import import_module

import pytest
from django.utils import timezone

from afritech.afripay.persistence import PersistentIdempotencyStore, PersistentTreasuryStore


def models():
    return import_module("afriride_system.django_app.apps.afripay.models")


@pytest.mark.django_db
def test_claim_creates_new_key():
    store = PersistentIdempotencyStore()

    item, created = store.claim("key.001", {"amount": 10})

    assert created is True
    assert item.key == "key.001"


@pytest.mark.django_db
def test_claim_reuse_same_payload_returns_existing():
    store = PersistentIdempotencyStore()

    store.claim("key.002", {"amount": 50})

    item, created = store.claim("key.002", {"amount": 50})

    assert created is False
    assert item.key == "key.002"


@pytest.mark.django_db
def test_claim_different_payload_raises_error():
    store = PersistentIdempotencyStore()

    store.claim("key.003", {"amount": 10})

    with pytest.raises(ValueError):
        store.claim("key.003", {"amount": 999})


@pytest.mark.django_db
def test_claim_expired_key_recreates():
    m = models()

    m.IdempotencyKey.objects.create(
        key="key.004",
        request_hash="old",
        expires_at=timezone.now() - timedelta(days=1),
    )

    store = PersistentIdempotencyStore()
    new_item, created = store.claim("key.004", {"amount": 20})

    assert created is True
    assert new_item.key == "key.004"


@pytest.mark.django_db
def test_store_and_get_response():
    store = PersistentIdempotencyStore()

    store.claim("key.005", {"amount": 10})
    store.store_response("key.005", {"status": "ok"})

    response = store.get_existing_response("key.005")

    assert response == {"status": "ok"}


@pytest.mark.django_db
def test_get_response_returns_none_if_not_completed():
    store = PersistentIdempotencyStore()

    store.claim("key.006", {"amount": 20})

    response = store.get_existing_response("key.006")

    assert response is None


@pytest.mark.django_db
def test_prune_expired_keys():
    m = models()

    m.IdempotencyKey.objects.create(
        key="key.expired",
        request_hash="x",
        expires_at=timezone.now() - timedelta(days=1),
    )

    store = PersistentIdempotencyStore()
    deleted = store.prune_expired()

    assert deleted >= 1


@pytest.mark.django_db
def test_reserve_success():
    m = models()

    m.LiquidityPool.objects.create(
        pool_id="pool.test",
        provider="mtn",
        currency="USD",
        balance=Decimal("100"),
        reserved=Decimal("0"),
        low_watermark=Decimal("10"),
    )

    store = PersistentTreasuryStore()
    pool = store.reserve("mtn", "usd", Decimal("30"))

    assert pool.reserved == Decimal("30")


@pytest.mark.django_db
def test_reserve_insufficient_liquidity():
    m = models()

    m.LiquidityPool.objects.create(
        pool_id="pool.test",
        provider="mtn",
        currency="USD",
        balance=Decimal("20"),
        reserved=Decimal("0"),
        low_watermark=Decimal("10"),
    )

    store = PersistentTreasuryStore()

    with pytest.raises(ValueError):
        store.reserve("mtn", "USD", Decimal("50"))


@pytest.mark.django_db
def test_settle_success():
    m = models()

    m.LiquidityPool.objects.create(
        pool_id="pool.test",
        provider="mtn",
        currency="USD",
        balance=Decimal("100"),
        reserved=Decimal("50"),
        low_watermark=Decimal("10"),
    )

    store = PersistentTreasuryStore()
    pool = store.settle("mtn", "USD", Decimal("50"))

    assert pool.balance == Decimal("50")
    assert pool.reserved == Decimal("0")


@pytest.mark.django_db
def test_settle_invalid_state():
    m = models()

    m.LiquidityPool.objects.create(
        pool_id="pool.test",
        provider="mtn",
        currency="USD",
        balance=Decimal("20"),
        reserved=Decimal("5"),
        low_watermark=Decimal("10"),
    )

    store = PersistentTreasuryStore()

    with pytest.raises(ValueError):
        store.settle("mtn", "USD", Decimal("50"))


@pytest.mark.django_db
def test_release_success():
    m = models()

    m.LiquidityPool.objects.create(
        pool_id="pool.test",
        provider="airtel",
        currency="USD",
        balance=Decimal("100"),
        reserved=Decimal("50"),
        low_watermark=Decimal("10"),
    )

    store = PersistentTreasuryStore()
    pool = store.release("airtel", "usd", Decimal("30"))

    assert pool.reserved == Decimal("20")


@pytest.mark.django_db
def test_release_invalid_amount():
    m = models()

    m.LiquidityPool.objects.create(
        pool_id="pool.test",
        provider="airtel",
        currency="USD",
        balance=Decimal("100"),
        reserved=Decimal("10"),
        low_watermark=Decimal("10"),
    )

    store = PersistentTreasuryStore()

    with pytest.raises(ValueError):
        store.release("airtel", "usd", Decimal("50"))
