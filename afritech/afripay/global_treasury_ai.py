"""Global treasury intelligence for multi-currency and on-chain advisory."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from afritech.afripay.events import canonical_hash
from afritech.afripay.treasury_ai import TreasuryAI, default_treasury_ai


def _decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _format(value: Decimal) -> str:
    return format(_decimal(value).quantize(Decimal("0.01")), ".2f")


def _percent(value: Decimal) -> str:
    return format(_decimal(value).quantize(Decimal("0.01")), ".2f")


def _currency_amounts(entries: tuple[Mapping[str, Any], ...], amount_key: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for entry in entries:
        currency = str(entry.get("currency") or "UNKNOWN").upper()
        totals[currency] = totals.get(currency, Decimal("0")) + _decimal(entry.get(amount_key))
    return totals


@dataclass(frozen=True)
class MultiCurrencyRecommendation:
    recommendation_id: str
    title: str
    action: str
    priority: str
    rationale: str

    def canonical(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "action": self.action,
            "priority": self.priority,
            "rationale": self.rationale,
        }


class GlobalTreasuryAI:
    """Advisory treasury intelligence across currencies and on-chain anchors."""

    authority_boundary = "advisory_only_and_policy_gated"

    def __init__(self, treasury_ai: TreasuryAI | None = None) -> None:
        self.treasury_ai = treasury_ai or default_treasury_ai()

    def evaluate(self, snapshot: Mapping[str, Any], *, base_currency: str = "USD") -> dict[str, Any]:
        base_currency = (base_currency or "USD").upper()
        liquidity_positions = tuple(snapshot.get("liquidity_positions") or ())
        prefunding_accounts = tuple(snapshot.get("prefunding_accounts") or ())
        settlement_exposures = tuple(snapshot.get("settlement_exposures") or ())

        core = self.treasury_ai.evaluate(snapshot)
        currency_totals = _currency_amounts(liquidity_positions, "available_balance")
        total_balance = sum(currency_totals.values(), Decimal("0"))
        base_balance = currency_totals.get(base_currency, Decimal("0"))
        foreign_balance = total_balance - base_balance
        fx_exposure = foreign_balance / total_balance if total_balance > 0 else Decimal("0")
        stablecoin_ratio = self._stablecoin_ratio(fx_exposure, total_balance)
        hedge_actions = self._hedge_actions(
            currency_totals=currency_totals,
            base_currency=base_currency,
            fx_exposure=fx_exposure,
            stablecoin_ratio=stablecoin_ratio,
        )
        onchain = self._onchain_plan(
            snapshot=snapshot,
            currency_totals=currency_totals,
            prefunding_accounts=prefunding_accounts,
            settlement_exposures=settlement_exposures,
        )
        recommendations = self._recommendations(core, hedge_actions, onchain)

        return {
            "classification": "NOVAPAY_GLOBAL_TREASURY_INTELLIGENCE_REPORT",
            "authority_boundary": self.authority_boundary,
            "core": core,
            "multi_currency": {
                "base_currency": base_currency,
                "currency_totals": {
                    currency: _format(amount) for currency, amount in sorted(currency_totals.items())
                },
                "currency_distribution": self._distribution(currency_totals),
                "fx_exposure": _percent(fx_exposure),
                "stablecoin_ratio": _percent(stablecoin_ratio),
                "stablecoin_target": self._stablecoin_target(core, total_balance, stablecoin_ratio, base_currency),
                "hedge_actions": hedge_actions,
                "action": self._multi_currency_action(fx_exposure, stablecoin_ratio),
            },
            "onchain": onchain,
            "recommendations": recommendations,
            "metrics": {
                "currency_count": len(currency_totals),
                "fx_exposure": _percent(fx_exposure),
                "stablecoin_ratio": _percent(stablecoin_ratio),
                "onchain_coverage": onchain["onchain_coverage"],
                "anchor_count": len(onchain["anchor_batch_plan"]),
            },
        }

    def _distribution(self, currency_totals: Mapping[str, Decimal]) -> list[dict[str, str]]:
        total = sum(currency_totals.values(), Decimal("0"))
        if total <= 0:
            return []
        distribution = []
        for currency, amount in sorted(currency_totals.items()):
            share = amount / total if total > 0 else Decimal("0")
            distribution.append(
                {
                    "currency": currency,
                    "amount": _format(amount),
                    "share": _percent(share * Decimal("100")),
                }
            )
        return distribution

    def _stablecoin_ratio(self, fx_exposure: Decimal, total_balance: Decimal) -> Decimal:
        if total_balance <= 0:
            return Decimal("0")
        if fx_exposure >= Decimal("0.60"):
            return Decimal("0.30")
        if fx_exposure >= Decimal("0.35"):
            return Decimal("0.20")
        if fx_exposure >= Decimal("0.20"):
            return Decimal("0.10")
        return Decimal("0.05")

    def _stablecoin_target(
        self,
        core: Mapping[str, Any],
        total_balance: Decimal,
        stablecoin_ratio: Decimal,
        base_currency: str,
    ) -> dict[str, str]:
        reserve = total_balance * stablecoin_ratio
        if core.get("risk_level") in {"HIGH", "CRITICAL"}:
            reserve = max(reserve, total_balance * Decimal("0.20"))
        return {
            "currency": f"STABLE_RESERVE_{base_currency}",
            "amount": _format(reserve),
            "strategy": "reserve_to_stablecoin",
        }

    def _hedge_actions(
        self,
        *,
        currency_totals: Mapping[str, Decimal],
        base_currency: str,
        fx_exposure: Decimal,
        stablecoin_ratio: Decimal,
    ) -> tuple[str, ...]:
        actions: list[str] = []
        if fx_exposure >= Decimal("0.35"):
            actions.append(f"convert_foreign_balance_to_{base_currency}_and_stable_reserve")
        if stablecoin_ratio >= Decimal("0.20"):
            actions.append("hedge_with_stablecoin_reserve")
        if any(currency not in {base_currency, "USD"} for currency in currency_totals):
            actions.append("rebalance_regional_balances")
        if not actions:
            actions.append("hold_position")
        return tuple(actions)

    def _multi_currency_action(self, fx_exposure: Decimal, stablecoin_ratio: Decimal) -> str:
        if fx_exposure >= Decimal("0.60"):
            return "convert_to_stablecoin_and_de-risk"
        if stablecoin_ratio >= Decimal("0.20"):
            return "rebalance_to_stable_reserve"
        if fx_exposure <= Decimal("0.10"):
            return "hold_position"
        return "partial_hedge"

    def _onchain_plan(
        self,
        *,
        snapshot: Mapping[str, Any],
        currency_totals: Mapping[str, Decimal],
        prefunding_accounts: tuple[Mapping[str, Any], ...],
        settlement_exposures: tuple[Mapping[str, Any], ...],
    ) -> dict[str, Any]:
        snapshot_root = str(
            snapshot.get("ledger_checkpoint", {}).get("snapshot_hash")
            or snapshot.get("global_ledger_root")
            or canonical_hash(snapshot)
        )
        anchor_batch_plan: list[dict[str, str]] = []
        for currency, amount in sorted(currency_totals.items()):
            proof_hash = canonical_hash(
                {
                    "kind": "treasury_currency_reserve",
                    "currency": currency,
                    "balance": _format(amount),
                    "snapshot_root": snapshot_root,
                }
            )
            anchor_batch_plan.append(
                {
                    "anchor_id": f"treasury.{currency.lower()}.{snapshot_root[:12]}",
                    "proof_hash": proof_hash,
                    "context": "TREASURY_CURRENCY",
                    "currency": currency,
                    "amount": _format(amount),
                }
            )

        treasury_summary_hash = canonical_hash(
            {
                "kind": "treasury_snapshot",
                "snapshot_root": snapshot_root,
                "prefunding_accounts": [
                    {
                        "provider": str(account.get("provider") or ""),
                        "currency": str(account.get("currency") or ""),
                        "current_balance": str(account.get("current_balance") or "0"),
                    }
                    for account in prefunding_accounts
                ],
                "settlement_exposures": [
                    {
                        "transfer_id": str(exposure.get("transfer_id") or ""),
                        "currency": str(exposure.get("currency") or ""),
                        "amount_pending": str(exposure.get("amount_pending") or "0"),
                    }
                    for exposure in settlement_exposures
                ],
            }
        )
        anchor_batch_plan.append(
            {
                "anchor_id": f"treasury.snapshot.{snapshot_root[:12]}",
                "proof_hash": treasury_summary_hash,
                "context": "TREASURY_SNAPSHOT",
                "currency": "MIXED",
                "amount": _format(sum(currency_totals.values(), Decimal("0"))),
            }
        )

        return {
            "batch_strategy": "anchorBatchV2",
            "verification_mode": "advisory_only",
            "snapshot_root": snapshot_root,
            "anchor_batch_plan": anchor_batch_plan,
            "batch_size": len(anchor_batch_plan),
            "onchain_coverage": "100.00" if anchor_batch_plan else "0.00",
            "ledger_anchor_context": "TREASURY_SNAPSHOT",
        }

    def _recommendations(
        self,
        core: Mapping[str, Any],
        hedge_actions: tuple[str, ...],
        onchain: Mapping[str, Any],
    ) -> tuple[dict[str, Any], ...]:
        recommendations: list[dict[str, Any]] = []
        for recommendation in core.get("recommendations", []):
            recommendations.append(dict(recommendation))
        for index, action in enumerate(hedge_actions, start=1):
            recommendations.append(
                MultiCurrencyRecommendation(
                    recommendation_id=f"global.multi_currency.{index}",
                    title=action.replace("_", " ").title(),
                    action=action,
                    priority="high" if index == 1 and action != "hold_position" else "medium",
                    rationale="Global treasury policy recommends a currency hedge action.",
                ).canonical()
            )
        recommendations.append(
            {
                "recommendation_id": "global.onchain.anchor",
                "title": "Anchor treasury snapshot batch",
                "action": "anchor_treasury_snapshot",
                "priority": "medium",
                "rationale": "Treasury records should be packaged for on-chain proof anchoring.",
                "batch_size": onchain["batch_size"],
            }
        )
        return tuple(recommendations)


def default_global_treasury_ai() -> GlobalTreasuryAI:
    return GlobalTreasuryAI()
