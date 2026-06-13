"""Adaptive multi-rail payment routing."""

from __future__ import annotations

from decimal import Decimal

from afritech.afripay.exceptions import GuardViolation
from afritech.afripay.guards import guard_quote
from afritech.afripay.models import PaymentRoute, ProviderQuote, new_id
from afritech.afripay.money import Money
from afritech.afripay.providers import PaymentProvider
from afritech.afripay.treasury import TreasuryEngine


class AdaptiveRoutingEngine:
    def __init__(
        self,
        providers: tuple[PaymentProvider, ...],
        treasury: TreasuryEngine | None = None,
    ) -> None:
        if not providers:
            raise GuardViolation("at least one provider is required")
        self.providers = providers
        self.treasury = treasury

    def plan_routes(
        self,
        *,
        transaction_id: str,
        amount: Money,
        preference: str = "balanced",
    ) -> tuple[PaymentRoute, ...]:
        amount.require_positive()
        quotes = [provider.quote(amount) for provider in self.providers]
        for quote in quotes:
            guard_quote(quote)
        planned = self._split(amount, quotes, preference)
        if sum(route_amount.amount for _, route_amount in planned) != amount.amount:
            raise GuardViolation("route split does not equal transaction amount")
        return tuple(
            PaymentRoute(
                route_id=new_id("route"),
                transaction_id=transaction_id,
                provider=quote.provider,
                rail=quote.rail,
                amount=route_amount,
                fee=Money.of(route_amount.amount * (quote.fee.amount / quote.amount.amount), amount.currency),
            )
            for quote, route_amount in planned
        )

    def _split(
        self,
        amount: Money,
        quotes: list[ProviderQuote],
        preference: str,
    ) -> list[tuple[ProviderQuote, Money]]:
        ranked = sorted(quotes, key=lambda quote: self._score(quote, preference))
        remaining = amount.amount
        planned: list[tuple[ProviderQuote, Money]] = []
        for quote in ranked:
            if remaining <= Decimal("0.00"):
                break
            liquidity = (
                self.treasury.available(quote.provider, amount.currency).amount
                if self.treasury is not None
                else quote.amount.amount
            )
            allocation = min(remaining, quote.amount.amount, liquidity)
            if allocation > Decimal("0.00"):
                planned.append((quote, Money.of(allocation, amount.currency)))
                remaining -= allocation
        if remaining != Decimal("0.00"):
            raise GuardViolation("provider capacity cannot cover amount")
        return planned

    def _score(self, quote: ProviderQuote, preference: str) -> Decimal:
        fee_ratio = quote.fee.amount / quote.amount.amount
        latency_score = Decimal(quote.estimated_latency_ms) / Decimal("10000")
        reliability_penalty = Decimal("1.00") - quote.reliability
        if preference == "cheapest":
            return (fee_ratio * Decimal("0.75")) + (latency_score * Decimal("0.10")) + reliability_penalty
        if preference == "fastest":
            return (latency_score * Decimal("0.75")) + (fee_ratio * Decimal("0.15")) + reliability_penalty
        if preference == "reliable":
            return (reliability_penalty * Decimal("0.75")) + fee_ratio + (latency_score * Decimal("0.10"))
        return (fee_ratio * Decimal("0.45")) + (latency_score * Decimal("0.25")) + (reliability_penalty * Decimal("0.30"))
