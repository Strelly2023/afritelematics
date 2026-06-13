"""Deterministic intelligence layer hooks for AfriPay."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from afritech.afripay.models import PaymentRoute, Transaction
from afritech.afripay.money import Money


@dataclass(frozen=True)
class FraudSignal:
    score: Decimal
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class LiquidityForecast:
    wallet_id: str
    currency: str
    days_until_shortfall: int | None
    recommended_topup: Money | None


class FraudDetector:
    def score(self, transaction: Transaction, recent_transactions: tuple[Transaction, ...] = ()) -> FraudSignal:
        score = Decimal("0.00")
        reasons: list[str] = []
        if transaction.amount.amount >= Decimal("5000.00"):
            score += Decimal("0.40")
            reasons.append("large_amount")
        same_payee = sum(1 for item in recent_transactions if item.payee_id == transaction.payee_id)
        if same_payee >= 5:
            score += Decimal("0.25")
            reasons.append("repeated_payee_velocity")
        if transaction.metadata.get("channel") == "offline" and transaction.amount.amount >= Decimal("500.00"):
            score += Decimal("0.20")
            reasons.append("large_offline_payment")
        return FraudSignal(min(score, Decimal("1.00")), tuple(reasons))


class LiquidityEngine:
    def forecast(
        self,
        *,
        wallet_id: str,
        current_balance: Money,
        average_daily_outflow: Money,
        safety_buffer_days: int = 3,
    ) -> LiquidityForecast:
        if average_daily_outflow.is_zero:
            return LiquidityForecast(wallet_id, current_balance.currency, None, None)
        days = int(current_balance.amount // average_daily_outflow.amount)
        recommended = None
        if days <= safety_buffer_days:
            recommended = average_daily_outflow.multiply(safety_buffer_days + 1) - current_balance
        return LiquidityForecast(wallet_id, current_balance.currency, days, recommended)


class RouteAnalytics:
    def summarize(self, routes: tuple[PaymentRoute, ...]) -> dict[str, object]:
        return {
            "route_count": len(routes),
            "providers": [route.provider for route in routes],
            "rails": [route.rail for route in routes],
            "total_fee": sum(route.fee.amount for route in routes),
            "max_latency_ms": max((route.latency_ms or 0 for route in routes), default=0),
        }


