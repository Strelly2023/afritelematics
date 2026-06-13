"""Treasury and liquidity controls for AfriPay."""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from afritech.afripay.events import EventStore
from afritech.afripay.exceptions import GuardViolation, InsufficientFunds
from afritech.afripay.money import Money


@dataclass(frozen=True)
class LiquidityPool:
    pool_id: str
    provider: str
    currency: str
    balance: Money
    reserved: Money
    low_watermark: Money

    @property
    def available(self) -> Money:
        return self.balance - self.reserved


@dataclass(frozen=True)
class TreasuryReservation:
    reservation_id: str
    provider: str
    currency: str
    amount: Money
    status: str = "reserved"


class TreasuryEngine:
    def __init__(
        self,
        pools: tuple[LiquidityPool, ...] = (),
        event_store: EventStore | None = None,
    ) -> None:
        self._pools = {(pool.provider, pool.currency): pool for pool in pools}
        self._reservations: dict[str, TreasuryReservation] = {}
        self.event_store = event_store or EventStore()

    def add_pool(
        self,
        *,
        pool_id: str,
        provider: str,
        balance: Money,
        low_watermark: Money | None = None,
    ) -> LiquidityPool:
        watermark = low_watermark or Money.of("0.00", balance.currency)
        pool = LiquidityPool(pool_id, provider, balance.currency, balance, Money.of("0.00", balance.currency), watermark)
        self._pools[(provider, balance.currency)] = pool
        self.event_store.append(
            "afripay.treasury.pool_added",
            {"pool_id": pool_id, "provider": provider, "balance": balance.canonical()},
        )
        return pool

    def available(self, provider: str, currency: str) -> Money:
        pool = self._pools.get((provider, currency.upper()))
        if pool is None:
            return Money.of("0.00", currency)
        return pool.available

    def reserve(self, provider: str, amount: Money, reservation_id: str) -> TreasuryReservation:
        amount.require_positive()
        key = (provider, amount.currency)
        pool = self._require_pool(key)
        if pool.available.amount < amount.amount:
            raise InsufficientFunds("insufficient provider liquidity")
        if reservation_id in self._reservations:
            raise GuardViolation("duplicate treasury reservation")
        updated = replace(pool, reserved=pool.reserved + amount)
        self._pools[key] = updated
        reservation = TreasuryReservation(reservation_id, provider, amount.currency, amount)
        self._reservations[reservation_id] = reservation
        self.event_store.append(
            "afripay.treasury.reserved",
            {"provider": provider, "reservation_id": reservation_id, "amount": amount.canonical()},
            aggregate_id=reservation_id,
        )
        return reservation

    def settle(self, reservation_id: str) -> TreasuryReservation:
        reservation = self._require_reservation(reservation_id, "reserved")
        key = (reservation.provider, reservation.currency)
        pool = self._require_pool(key)
        updated = replace(
            pool,
            balance=pool.balance - reservation.amount,
            reserved=pool.reserved - reservation.amount,
        )
        self._pools[key] = updated
        settled = replace(reservation, status="settled")
        self._reservations[reservation_id] = settled
        self.event_store.append(
            "afripay.treasury.settled",
            {"provider": reservation.provider, "reservation_id": reservation_id, "amount": reservation.amount.canonical()},
            aggregate_id=reservation_id,
        )
        return settled

    def release(self, reservation_id: str) -> TreasuryReservation:
        reservation = self._require_reservation(reservation_id, "reserved")
        key = (reservation.provider, reservation.currency)
        pool = self._require_pool(key)
        self._pools[key] = replace(pool, reserved=pool.reserved - reservation.amount)
        released = replace(reservation, status="released")
        self._reservations[reservation_id] = released
        self.event_store.append(
            "afripay.treasury.released",
            {"provider": reservation.provider, "reservation_id": reservation_id},
            aggregate_id=reservation_id,
        )
        return released

    def liquidity_alerts(self) -> tuple[dict[str, object], ...]:
        alerts = []
        for pool in self._pools.values():
            if pool.available.amount <= pool.low_watermark.amount:
                alerts.append(
                    {
                        "pool_id": pool.pool_id,
                        "provider": pool.provider,
                        "currency": pool.currency,
                        "available": pool.available.canonical(),
                        "low_watermark": pool.low_watermark.canonical(),
                    }
                )
        return tuple(alerts)

    def pools(self) -> tuple[LiquidityPool, ...]:
        return tuple(self._pools.values())

    def _require_pool(self, key: tuple[str, str]) -> LiquidityPool:
        pool = self._pools.get(key)
        if pool is None:
            raise InsufficientFunds("missing provider liquidity pool")
        return pool

    def _require_reservation(self, reservation_id: str, status: str) -> TreasuryReservation:
        reservation = self._reservations.get(reservation_id)
        if reservation is None:
            raise GuardViolation("unknown treasury reservation")
        if reservation.status != status:
            raise GuardViolation(f"treasury reservation is not {status}")
        return reservation


def default_treasury_engine() -> TreasuryEngine:
    treasury = TreasuryEngine()
    treasury.add_pool(
        pool_id="pool.mtn.aud",
        provider="mtn_mobile_money",
        balance=Money.of("70.00", "AUD"),
        low_watermark=Money.of("10.00", "AUD"),
    )
    treasury.add_pool(
        pool_id="pool.bank.aud",
        provider="bank_partner",
        balance=Money.of("5000.00", "AUD"),
        low_watermark=Money.of("100.00", "AUD"),
    )
    treasury.add_pool(
        pool_id="pool.stablecoin.aud",
        provider="stablecoin_settlement",
        balance=Money.of("250.00", "AUD"),
        low_watermark=Money.of("50.00", "AUD"),
    )
    return treasury
