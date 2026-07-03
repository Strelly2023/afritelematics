"""Treasury intelligence and financial advisory for AfriPay."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


def _decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _format(value: Decimal) -> str:
    return format(_decimal(value).quantize(Decimal("0.01")), ".2f")


def _risk_level(coverage_ratio: Decimal, settlement_pressure: Decimal) -> str:
    if coverage_ratio < Decimal("1.00") or settlement_pressure >= Decimal("0.90"):
        return "CRITICAL"
    if coverage_ratio < Decimal("1.20") or settlement_pressure >= Decimal("0.70"):
        return "HIGH"
    if coverage_ratio < Decimal("1.50") or settlement_pressure >= Decimal("0.45"):
        return "MEDIUM"
    return "LOW"


@dataclass(frozen=True)
class TreasuryRecommendation:
    recommendation_id: str
    title: str
    action: str
    priority: str
    rationale: str
    provider: str | None = None
    currency: str | None = None

    def canonical(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "action": self.action,
            "priority": self.priority,
            "rationale": self.rationale,
            "provider": self.provider,
            "currency": self.currency,
        }


class TreasuryAI:
    """Deterministic treasury advisor.

    The advisor consumes the governed treasury snapshot and produces only
    recommendations. It does not move funds, mutate ledger state, or call
    external banks or payment processors.
    """

    authority_boundary = "advisory_only_and_policy_gated"

    def evaluate(self, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        liquidity_positions = tuple(snapshot.get("liquidity_positions") or ())
        prefunding_accounts = tuple(snapshot.get("prefunding_accounts") or ())
        settlement_exposures = tuple(snapshot.get("settlement_exposures") or ())

        available_liquidity = sum(
            _decimal(position.get("available_balance"))
            for position in liquidity_positions
        )
        reserved_liquidity = sum(
            _decimal(position.get("reserved_balance"))
            for position in liquidity_positions
        )
        settlement_obligations = sum(
            _decimal(exposure.get("amount_pending"))
            for exposure in settlement_exposures
            if str(exposure.get("status", "pending")).lower() in {"pending", "queued", "open"}
        )
        prefunding_gap = sum(
            max(_decimal(account.get("required_balance")) - _decimal(account.get("current_balance")), Decimal("0"))
            for account in prefunding_accounts
        )

        total_obligations = settlement_obligations + prefunding_gap
        coverage_ratio = (
            available_liquidity / total_obligations if total_obligations > 0 else Decimal("99.99")
        )
        settlement_pressure = (
            settlement_obligations / available_liquidity if available_liquidity > 0 else Decimal("1.00")
        )
        reserve_headroom = available_liquidity - total_obligations
        risk_level = _risk_level(coverage_ratio, settlement_pressure)

        decision = self._decision(
            coverage_ratio=coverage_ratio,
            risk_level=risk_level,
            reserve_headroom=reserve_headroom,
            settlement_pressure=settlement_pressure,
        )

        recommendations = self._recommendations(
            prefunding_accounts=prefunding_accounts,
            liquidity_positions=liquidity_positions,
            settlement_exposures=settlement_exposures,
            coverage_ratio=coverage_ratio,
            reserve_headroom=reserve_headroom,
        )

        stress_tests = self._stress_tests(
            available_liquidity=available_liquidity,
            total_obligations=total_obligations,
            settlement_obligations=settlement_obligations,
            reserved_liquidity=reserved_liquidity,
        )

        return {
            "classification": "NOVAPAY_TREASURY_AI_REPORT",
            "authority_boundary": self.authority_boundary,
            "risk_level": risk_level,
            "cash_balance": _format(available_liquidity),
            "reserved_balance": _format(reserved_liquidity),
            "settlement_obligations": _format(settlement_obligations),
            "prefunding_gap": _format(prefunding_gap),
            "coverage_ratio": _format(coverage_ratio),
            "settlement_pressure": _format(settlement_pressure),
            "reserve_headroom": _format(reserve_headroom),
            "decision": decision,
            "recommendations": [recommendation.canonical() for recommendation in recommendations],
            "stress_tests": stress_tests,
            "provider_snapshot": self._provider_snapshot(prefunding_accounts, settlement_exposures),
        }

    def _decision(
        self,
        *,
        coverage_ratio: Decimal,
        risk_level: str,
        reserve_headroom: Decimal,
        settlement_pressure: Decimal,
    ) -> dict[str, str]:
        if risk_level == "CRITICAL":
            return {
                "action": "increase_liquidity",
                "method": "hold_cash_reserve_and_delay_non_critical_payouts",
                "reason": "Coverage is below safe operating levels.",
                "priority": "critical",
            }
        if risk_level == "HIGH":
            return {
                "action": "rebalance_treasury",
                "method": "shift_reserves_to_settlement_pools",
                "reason": "Settlement pressure is elevated and prefunding needs attention.",
                "priority": "high",
            }
        if reserve_headroom > Decimal("0") and coverage_ratio > Decimal("2.00") and settlement_pressure < Decimal("0.20"):
            return {
                "action": "invest_growth",
                "method": "release_excess_capital_for_growth",
                "reason": "Liquidity is healthy and reserve headroom is strong.",
                "priority": "low",
            }
        return {
            "action": "maintain_buffer",
            "method": "keep_current_treasury_policy",
            "reason": "Liquidity and obligations remain within target range.",
            "priority": "medium",
        }

    def _recommendations(
        self,
        *,
        prefunding_accounts: tuple[Mapping[str, Any], ...],
        liquidity_positions: tuple[Mapping[str, Any], ...],
        settlement_exposures: tuple[Mapping[str, Any], ...],
        coverage_ratio: Decimal,
        reserve_headroom: Decimal,
    ) -> tuple[TreasuryRecommendation, ...]:
        recommendations: list[TreasuryRecommendation] = []

        if reserve_headroom < Decimal("0"):
            recommendations.append(
                TreasuryRecommendation(
                    recommendation_id="treasury.reserve.topup",
                    title="Top up treasury reserves",
                    action="hold_more_cash",
                    priority="critical",
                    rationale="Treasury obligations exceed available liquidity.",
                )
            )

        low_prefunding = [
            account
            for account in prefunding_accounts
            if _decimal(account.get("current_balance")) < _decimal(account.get("required_balance"))
        ]
        for account in low_prefunding[:3]:
            recommendations.append(
                TreasuryRecommendation(
                    recommendation_id=f"prefunding.{account.get('provider')}.{account.get('currency')}",
                    title=f"Rebalance {account.get('provider')} prefunding",
                    action="rebalance_prefunding",
                    priority="high",
                    rationale="Provider funding is below required balance.",
                    provider=str(account.get("provider")),
                    currency=str(account.get("currency")),
                )
            )

        if settlement_exposures and coverage_ratio >= Decimal("1.50"):
            recommendations.append(
                TreasuryRecommendation(
                    recommendation_id="treasury.settlement.diversify",
                    title="Diversify settlement rails",
                    action="balance_settlement_risk",
                    priority="medium",
                    rationale="Multiple settlement exposures are covered, so reserve concentration can be reduced.",
                )
            )

        if liquidity_positions and coverage_ratio > Decimal("2.00"):
            recommendations.append(
                TreasuryRecommendation(
                    recommendation_id="treasury.growth.allocate",
                    title="Allocate surplus capital to growth",
                    action="invest_growth",
                    priority="low",
                    rationale="Liquidity exceeds obligations by a wide margin.",
                )
            )

        if not recommendations:
            recommendations.append(
                TreasuryRecommendation(
                    recommendation_id="treasury.buffer.monitor",
                    title="Monitor treasury buffers",
                    action="continue_monitoring",
                    priority="low",
                    rationale="Treasury controls remain stable and no immediate action is required.",
                )
            )

        return tuple(recommendations)

    def _stress_tests(
        self,
        *,
        available_liquidity: Decimal,
        total_obligations: Decimal,
        settlement_obligations: Decimal,
        reserved_liquidity: Decimal,
    ) -> tuple[dict[str, Any], ...]:
        scenarios = []
        shocks = (
            ("payment_processor_failure", Decimal("0.85"), "switch_to_backup_processor"),
            ("10_percent_settlement_surge", Decimal("0.90"), "delay_non_critical_payouts"),
            ("5_percent_liquidity_shock", Decimal("0.95"), "increase_cash_reserve"),
        )
        for scenario, multiplier, mitigation in shocks:
            projected_cash = available_liquidity * multiplier
            projected_obligations = total_obligations + (settlement_obligations * (Decimal("1.00") - multiplier))
            projected_coverage = (
                projected_cash / projected_obligations if projected_obligations > 0 else Decimal("99.99")
            )
            scenarios.append(
                {
                    "scenario": scenario,
                    "projected_cash_balance": _format(projected_cash),
                    "projected_coverage_ratio": _format(projected_coverage),
                    "impact": "CRITICAL"
                    if projected_coverage < Decimal("1.00")
                    else "HIGH"
                    if projected_coverage < Decimal("1.20")
                    else "MEDIUM"
                    if projected_coverage < Decimal("1.50")
                    else "LOW",
                    "mitigation": mitigation,
                    "reserved_balance": _format(reserved_liquidity),
                }
            )
        return tuple(scenarios)

    def _provider_snapshot(
        self,
        prefunding_accounts: tuple[Mapping[str, Any], ...],
        settlement_exposures: tuple[Mapping[str, Any], ...],
    ) -> tuple[dict[str, Any], ...]:
        exposure_by_key: dict[tuple[str, str], Decimal] = {}
        for exposure in settlement_exposures:
            provider = str(exposure.get("provider") or exposure.get("corridor_id") or "unknown")
            currency = str(exposure.get("currency") or "unknown")
            exposure_by_key[(provider, currency)] = exposure_by_key.get((provider, currency), Decimal("0")) + _decimal(
                exposure.get("amount_pending")
            )

        providers = []
        for account in prefunding_accounts:
            provider = str(account.get("provider") or "unknown")
            currency = str(account.get("currency") or "unknown")
            required = _decimal(account.get("required_balance"))
            current = _decimal(account.get("current_balance"))
            providers.append(
                {
                    "provider": provider,
                    "currency": currency,
                    "required_balance": _format(required),
                    "current_balance": _format(current),
                    "prefunding_gap": _format(max(required - current, Decimal("0"))),
                    "pending_exposure": _format(exposure_by_key.get((provider, currency), Decimal("0"))),
                    "status": str(account.get("status") or "healthy"),
                }
            )

        return tuple(providers)


def default_treasury_ai() -> TreasuryAI:
    return TreasuryAI()
