from __future__ import annotations

from decimal import Decimal
from importlib import import_module

import pytest
from hypothesis import given, settings, strategies as st

from afritech.afripay.money import Money
from afritech.afripay.persistence import _payload_hash, PersistentTreasuryStore


def models():
    return import_module("afriride_system.django_app.apps.afripay.models")


payload_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=8),
    values=st.one_of(
        st.integers(min_value=0, max_value=1000),
        st.text(min_size=0, max_size=16),
        st.booleans(),
    ),
    max_size=6,
)


amount_strategy = st.decimals(
    min_value=Decimal("0.01"),
    max_value=Decimal("150.00"),
    places=2,
)


@given(payload=payload_strategy)
def test_payload_hash_is_order_independent(payload):
    assert _payload_hash(payload) == _payload_hash(dict(reversed(list(payload.items()))))


@given(payload=payload_strategy)
def test_payload_hash_changes_when_payload_changes(payload):
    mutated = dict(payload)
    mutated["__sentinel__"] = "changed"

    assert _payload_hash(payload) != _payload_hash(mutated)


@pytest.mark.django_db(transaction=True)
@given(reserve_amount=amount_strategy, release_amount=amount_strategy)
@settings(max_examples=25)
def test_treasury_invariants_hold_after_reserve_and_release(reserve_amount, release_amount):
    m = models()
    m.LiquidityPool.objects.filter(provider="mtn", currency="USD").delete()
    m.LiquidityPool.objects.create(
        pool_id="pool.prop",
        provider="mtn",
        currency="USD",
        balance=Decimal("200.00"),
        reserved=Decimal("0.00"),
        low_watermark=Decimal("10.00"),
    )

    store = PersistentTreasuryStore()
    reserve_amount = min(reserve_amount, Decimal("150.00"))
    release_amount = min(release_amount, reserve_amount)

    pool = store.reserve("mtn", "usd", reserve_amount)
    assert pool.balance >= Decimal("0.00")
    assert pool.reserved >= Decimal("0.00")
    assert pool.reserved <= pool.balance + pool.reserved

    released = store.release("mtn", "usd", release_amount)
    assert released.balance >= Decimal("0.00")
    assert released.reserved >= Decimal("0.00")
    assert released.reserved <= released.balance + released.reserved


@pytest.mark.django_db(transaction=True)
@given(reserve_amount=amount_strategy)
@settings(max_examples=25)
def test_treasury_settle_never_breaks_balance_invariant(reserve_amount):
    m = models()
    reserve_amount = min(reserve_amount, Decimal("100.00"))
    m.LiquidityPool.objects.filter(provider="airtel", currency="USD").delete()
    m.LiquidityPool.objects.create(
        pool_id="pool.prop.settle",
        provider="airtel",
        currency="USD",
        balance=Decimal("200.00"),
        reserved=reserve_amount,
        low_watermark=Decimal("10.00"),
    )

    store = PersistentTreasuryStore()
    pool = store.settle("airtel", "usd", reserve_amount)

    assert pool.balance >= Decimal("0.00")
    assert pool.reserved >= Decimal("0.00")
    assert pool.reserved <= pool.balance + pool.reserved
