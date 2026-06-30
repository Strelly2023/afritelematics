"""Autonomous economic, simulation, and governance helpers.

This module sits above the bounded agent control plane. It is intentionally
deterministic and conservative: the economic market is simulated rather than
real, the digital twin is projection-only, and the governance protocol only
adjusts bounded policy values.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any, Mapping
import json
import time


MAX_SIMULATION_DEPTH = 1
MAX_TOTAL_RESOURCES = 5.0
GOVERNANCE_EPOCH_SECONDS = 60 * 60


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _action_name(action_bundle: Mapping[str, Any], key: str, default: str) -> str:
    section = action_bundle.get(key) or {}
    if isinstance(section, Mapping):
        return str(section.get("action") or default)
    return default


@dataclass(frozen=True)
class ResourceTrade:
    resource: str
    buyer: str
    seller: str
    requested: float
    price: float
    accepted: bool
    reason: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "resource": self.resource,
            "buyer": self.buyer,
            "seller": self.seller,
            "requested": round(float(self.requested), 4),
            "price": round(float(self.price), 4),
            "accepted": self.accepted,
            "reason": self.reason,
        }


class ResourceMarket:
    """Simulated market for internal resource exchange decisions."""

    def quote(
        self,
        *,
        resource: str,
        demand: float,
        supply: float,
        risk: float,
        cost_pressure: float,
    ) -> dict[str, Any]:
        demand = max(0.0, _safe_float(demand))
        supply = max(0.0, _safe_float(supply))
        risk = _clamp(_safe_float(risk), 0.0, 1.0)
        cost_pressure = _clamp(_safe_float(cost_pressure), 0.0, 1.5)
        scarcity = 1.0 if supply <= 0.0 else _clamp(demand / max(1.0, supply), 0.5, 2.0)
        base_price = 1.0 + (scarcity * 0.45) + (risk * 0.35) + (cost_pressure * 0.25)
        return {
            "resource": resource,
            "demand": round(demand, 4),
            "supply": round(supply, 4),
            "scarcity": round(scarcity, 4),
            "price": round(base_price, 4),
        }

    def trade(
        self,
        *,
        buyer: str,
        seller: str,
        resource: str,
        requested: float,
        budget: float,
        risk: float,
        cost_pressure: float,
    ) -> ResourceTrade:
        quote = self.quote(
            resource=resource,
            demand=requested,
            supply=max(1.0, requested * 1.25),
            risk=risk,
            cost_pressure=cost_pressure,
        )
        scarcity = _safe_float(quote.get("scarcity"), 1.0)
        force_rejection = scarcity > 2.0
        price = quote["price"] * max(1.0, _safe_float(requested))
        accepted = (not force_rejection) and price <= max(0.0, _safe_float(budget))
        reason = "accepted_within_budget" if accepted else "rejected_over_budget"
        if force_rejection:
            reason = "rejected_scarcity_guard"
        return ResourceTrade(
            resource=resource,
            buyer=buyer,
            seller=seller,
            requested=max(0.0, _safe_float(requested)),
            price=round(price, 4),
            accepted=accepted,
            reason=reason,
        )

    def negotiate(self, features: Mapping[str, Any], action_bundle: Mapping[str, Any]) -> dict[str, Any]:
        base_limit = max(1.0, _safe_float(features.get("sla_current"), 1.0))
        latency_ms = max(0.0, _safe_float(features.get("latency_ms")))
        cost_pressure = _clamp(_safe_float(features.get("cost_pressure")), 0.0, 1.5)
        risk = 1.0 if bool(features.get("anomaly", False)) else _clamp(_safe_float(features.get("risk_score")), 0.0, 1.0)
        region_load = _clamp(_safe_float(features.get("region_load")), 0.0, 3.0)
        budget = max(1.0, base_limit / 50.0)

        trade_plan = [
            (
                "compute_tokens",
                max(0.5, base_limit / 250.0),
                "sla" if _action_name(action_bundle, "policy", "maintain") in {"increase_limit", "maintain"} else "market",
            ),
            (
                "latency_priority_tokens",
                1.0 if _action_name(action_bundle, "routing", "keep_region") == "reroute_region" else 0.4,
                "routing",
            ),
            (
                "bandwidth_tokens",
                max(0.5, region_load * 0.75),
                "network",
            ),
            (
                "risk_buffer_tokens",
                1.0 if bool(features.get("anomaly", False)) else 0.25,
                "risk",
            ),
        ]

        trades: list[ResourceTrade] = []
        total_requested = 0.0
        total_price = 0.0
        for resource, requested, seller in trade_plan:
            if total_requested >= MAX_TOTAL_RESOURCES:
                break
            allowed_requested = min(requested, max(0.0, MAX_TOTAL_RESOURCES - total_requested))
            trade = self.trade(
                buyer="control_plane",
                seller=seller,
                resource=resource,
                requested=allowed_requested,
                budget=max(0.5, budget - total_price),
                risk=risk,
                cost_pressure=cost_pressure,
            )
            total_requested += allowed_requested
            total_price += trade.price if trade.accepted else 0.0
            trades.append(trade)

        accepted_count = sum(1 for trade in trades if trade.accepted)
        surplus = max(0.0, budget - total_price)
        return {
            "mode": "simulated_exchange",
            "budget": round(budget, 4),
            "total_price": round(total_price, 4),
            "surplus": round(surplus, 4),
            "accepted_trades": accepted_count,
            "total_requested": round(total_requested, 4),
            "trades": [trade.canonical_dict() for trade in trades],
            "resource_targets": {
                "compute_tokens": round(max(0.5, base_limit / 250.0), 4),
                "latency_priority_tokens": round(1.0 if _action_name(action_bundle, "routing", "keep_region") == "reroute_region" else 0.4, 4),
                "bandwidth_tokens": round(max(0.5, region_load * 0.75), 4),
                "risk_buffer_tokens": round(1.0 if bool(features.get("anomaly", False)) else 0.25, 4),
            },
            "guardrails": {
                "budget_cap": round(budget, 4),
                "risk": round(risk, 4),
                "cost_pressure": round(cost_pressure, 4),
                "latency_ms": round(latency_ms, 4),
                "max_total_resources": MAX_TOTAL_RESOURCES,
            },
        }


class DigitalTwin:
    """Projection-only model of the control plane."""

    def simulate(
        self,
        features: Mapping[str, Any],
        action_bundle: Mapping[str, Any],
        market_state: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        market = _safe_mapping(market_state)
        current = {
            "latency_ms": max(0.0, _safe_float(features.get("latency_ms"))),
            "cost_pressure": _clamp(_safe_float(features.get("cost_pressure")), 0.0, 1.5),
            "region_load": _clamp(_safe_float(features.get("region_load")), 0.0, 3.0),
            "errors": max(0.0, _safe_float(features.get("errors"))),
            "sla_current": max(1.0, _safe_float(features.get("sla_current"), 1.0)),
            "risk_score": _clamp(_safe_float(features.get("risk_score")), 0.0, 1.0),
        }
        policy_action = _action_name(action_bundle, "policy", "maintain")
        routing_action = _action_name(action_bundle, "routing", "keep_region")
        cost_action = _action_name(action_bundle, "cost", "hold_cost")
        risk_action = _action_name(action_bundle, "risk", "hold")

        projected = dict(current)
        if policy_action == "increase_limit":
            projected["latency_ms"] *= 0.92
            projected["region_load"] *= 0.92
            projected["cost_pressure"] *= 1.08
        elif policy_action == "decrease_limit":
            projected["latency_ms"] *= 1.08
            projected["region_load"] *= 1.04
            projected["cost_pressure"] *= 0.96

        if routing_action == "reroute_region":
            projected["latency_ms"] *= 0.8
            projected["region_load"] *= 0.88
        elif routing_action == "keep_region":
            projected["latency_ms"] *= 1.01

        if cost_action == "reduce_cost":
            projected["cost_pressure"] *= 0.88
        elif cost_action == "scale_cost":
            projected["cost_pressure"] *= 1.06

        if risk_action == "throttle":
            projected["errors"] *= 0.65
            projected["risk_score"] *= 0.75
        elif risk_action == "escalate":
            projected["risk_score"] *= 0.9

        projected["latency_ms"] = min(float(projected["latency_ms"]), 2000.0)
        projected["cost_pressure"] = min(float(projected["cost_pressure"]), 2.0)

        accepted_trades = _safe_int(market.get("accepted_trades"))
        surplus = _safe_float(market.get("surplus"))
        total_price = _safe_float(market.get("total_price"))
        execution_score = (
            1.0
            - min(2.0, projected["errors"] * 0.35)
            - min(1.25, max(0.0, projected["latency_ms"] - current["latency_ms"]) / 120.0)
            - min(1.0, max(0.0, projected["cost_pressure"] - current["cost_pressure"]))
            + min(0.5, surplus / max(1.0, market.get("budget", 1.0)))
            + min(0.35, accepted_trades * 0.08)
        )
        learning_reward = (
            (1.0 - min(1.0, max(0.0, projected["risk_score"] - current["risk_score"]))) * 0.6
            + (1.0 - min(1.0, max(0.0, projected["cost_pressure"] - current["cost_pressure"]))) * 0.4
        )
        confidence = _clamp(
            1.0 - min(1.0, abs(projected["latency_ms"] - current["latency_ms"]) / max(1.0, current["latency_ms"] + 1.0)),
            0.1,
            0.99,
        )
        confidence = _clamp((confidence + (0.5 + min(0.5, accepted_trades * 0.1))) / 2.0, 0.1, 0.99)
        decision = {
            "policy": _action_name(action_bundle, "policy", "maintain"),
            "routing": _action_name(action_bundle, "routing", "keep_region"),
            "cost": _action_name(action_bundle, "cost", "hold_cost"),
            "risk": _action_name(action_bundle, "risk", "hold"),
        }
        decision_hash = sha256(_canonical_json({**decision, "projected": projected, "mode": "projection_only"})).hexdigest()
        consensus_votes = _safe_int(features.get("consensus_votes"), 3)
        consensus_required = _safe_int(features.get("consensus_required"), 2)
        consensus_applied = consensus_votes >= consensus_required

        return {
            "mode": "projection_only",
            "current": {key: round(float(value), 4) for key, value in current.items()},
            "projected": {key: round(float(value), 4) for key, value in projected.items()},
            "execution_score": round(execution_score, 4),
            "learning_reward": round(learning_reward, 4),
            "confidence": round(confidence, 4),
            "market_surplus": round(surplus, 4),
            "market_spend": round(total_price, 4),
            "decision": decision,
            "decision_hash": decision_hash,
            "consensus": {
                "required_majority": consensus_required,
                "observed_votes": consensus_votes,
                "applied": consensus_applied,
            },
            "explainability": {
                "reason": "projection validated by bounded market and twin",
                "agents": {
                    "sla": decision["policy"],
                    "routing": decision["routing"],
                    "cost": decision["cost"],
                    "risk": decision["risk"],
                },
            },
            "simulation_depth": MAX_SIMULATION_DEPTH,
        }


class GovernanceProtocol:
    """Self-evolving but bounded governance policy."""

    def evolve(
        self,
        *,
        current_policy: Mapping[str, Any],
        performance_metrics: Mapping[str, Any],
        twin_projection: Mapping[str, Any],
        guardrails: Mapping[str, Any],
    ) -> dict[str, Any]:
        policy = _safe_mapping(current_policy)
        metrics = _safe_mapping(performance_metrics)
        twin = _safe_mapping(twin_projection)
        bounds = _safe_mapping(guardrails)
        current_epoch = int(time.time() // GOVERNANCE_EPOCH_SECONDS)
        previous_epoch_raw = policy.get("policy_epoch")
        previous_epoch = _safe_int(previous_epoch_raw, current_epoch - 1)
        if previous_epoch_raw is not None and previous_epoch == current_epoch:
            return {
                "mode": "self_evolving_guarded",
                "policy": {
                    "max_requests": max(1, _safe_int(policy.get("max_requests"), _safe_int(bounds.get("hard_cap"), 10_000))),
                    "risk_threshold": round(_clamp(_safe_float(policy.get("risk_threshold"), 0.7), 0.05, 0.95), 4),
                    "limit_multiplier": round(_clamp(_safe_float(policy.get("limit_multiplier"), 1.0), 0.5, 1.2), 4),
                    "policy_epoch": current_epoch,
                },
                "reason": "epoch_locked",
                "approved": True,
                "risk_score": round(_clamp(_safe_float(metrics.get("risk_score")), 0.0, 1.5), 4),
            }

        max_requests = max(1.0, _safe_float(policy.get("max_requests"), _safe_float(bounds.get("hard_cap"), 10_000)))
        risk_threshold = _clamp(_safe_float(policy.get("risk_threshold"), 0.7), 0.05, 0.95)
        limit_multiplier = _clamp(_safe_float(policy.get("limit_multiplier"), 1.0), 0.5, 1.2)

        failure_rate = _clamp(_safe_float(metrics.get("failure_rate")), 0.0, 1.5)
        stability = _clamp(_safe_float(metrics.get("stability"), 1.0), 0.0, 1.5)
        projected_latency = _safe_float(twin.get("projected", {}).get("latency_ms"), _safe_float(metrics.get("latency_ms")))
        projected_cost = _safe_float(twin.get("projected", {}).get("cost_pressure"), _safe_float(metrics.get("cost_pressure")))
        risk_score = _clamp(_safe_float(metrics.get("risk_score")), 0.0, 1.5)

        reason = "maintain"
        if failure_rate > 0.15 or risk_score > risk_threshold or projected_latency > 150:
            max_requests *= 0.9
            risk_threshold *= 0.92
            limit_multiplier *= 0.9
            reason = "protective_contraction"
        elif stability > 0.8 and projected_cost < 1.0 and projected_latency < 100:
            max_requests *= 1.05
            risk_threshold *= 1.02
            limit_multiplier *= 1.02
            reason = "measured_expansion"

        max_cap = max(1, _safe_int(bounds.get("hard_cap"), 10_000))
        min_cap = max(1, _safe_int(bounds.get("min_cap"), 1))
        max_requests = max(min_cap, min(max_cap, int(round(max_requests))))
        risk_threshold = _clamp(risk_threshold, 0.05, 0.95)
        limit_multiplier = _clamp(limit_multiplier, 0.5, 1.2)

        return {
            "mode": "self_evolving_guarded",
            "policy": {
                "max_requests": max_requests,
                "risk_threshold": round(risk_threshold, 4),
                "limit_multiplier": round(limit_multiplier, 4),
                "policy_epoch": current_epoch,
            },
            "reason": reason,
            "approved": reason != "protective_contraction" or failure_rate <= 0.5,
            "risk_score": round(risk_score, 4),
        }


class AutonomousEcosystem:
    """Composes market, twin, and governance layers into one bounded bundle."""

    def __init__(self) -> None:
        self.market = ResourceMarket()
        self.twin = DigitalTwin()
        self.governance = GovernanceProtocol()
        self._last_governance_policy: dict[str, Any] | None = None

    def evaluate(
        self,
        *,
        features: Mapping[str, Any],
        action_bundle: Mapping[str, Any],
        base_score: float,
    ) -> dict[str, Any]:
        market = self.market.negotiate(features, action_bundle)
        twin = self.twin.simulate(features, action_bundle, market)
        previous_policy = self._last_governance_policy or {}
        governance = self.governance.evolve(
            current_policy={
                "max_requests": _safe_float(previous_policy.get("max_requests"), _safe_float(features.get("sla_current"), 1.0)),
                "risk_threshold": _safe_float(previous_policy.get("risk_threshold"), _safe_float(features.get("risk_threshold"), 0.7)),
                "limit_multiplier": _safe_float(previous_policy.get("limit_multiplier"), _safe_float(action_bundle.get("limit_multiplier"), 1.0)),
                "policy_epoch": previous_policy.get("policy_epoch"),
            },
            performance_metrics={
                "failure_rate": min(1.0, _safe_float(features.get("errors")) / max(1.0, _safe_float(features.get("sla_current"), 1.0))),
                "stability": max(0.0, 1.0 - _clamp(_safe_float(features.get("errors")), 0.0, 5.0) * 0.2),
                "latency_ms": _safe_float(features.get("latency_ms")),
                "cost_pressure": _safe_float(features.get("cost_pressure")),
                "risk_score": _safe_float(features.get("risk_score")),
            },
            twin_projection=twin,
            guardrails=action_bundle.get("guardrails") or {},
        )

        market_bonus = market["surplus"] * 0.25 + market["accepted_trades"] * 0.08
        twin_bonus = twin["execution_score"] * 0.5 + twin["confidence"] * 0.15
        governance_bonus = 0.1 if governance["approved"] else -0.2
        execution_score = round(float(base_score) + market_bonus, 4)
        learning_reward = round(twin["learning_reward"] * 0.6 + governance_bonus * 0.4, 4)
        confidence = round(_clamp((twin["confidence"] + (1.0 if governance["approved"] else 0.0)) / 2.0, 0.1, 0.99), 4)
        composite_score = round(execution_score + twin_bonus + governance_bonus, 4)
        self._last_governance_policy = dict(governance.get("policy") or {})
        return {
            "score": execution_score,
            "execution_score": execution_score,
            "learning_reward": learning_reward,
            "composite_score": composite_score,
            "confidence": confidence,
            "market": market,
            "digital_twin": twin,
            "governance": governance,
            "explainability": {
                "decision": _action_name(action_bundle, "policy", "maintain"),
                "score": execution_score,
                "learning_reward": learning_reward,
                "composite_score": composite_score,
                "agents": {
                    "sla": _action_name(action_bundle, "policy", "maintain"),
                    "routing": _action_name(action_bundle, "routing", "keep_region"),
                    "cost": _action_name(action_bundle, "cost", "hold_cost"),
                    "risk": _action_name(action_bundle, "risk", "hold"),
                },
                "economy": market,
                "twin": twin,
                "governance": governance,
                "confidence": confidence,
            },
        }


__all__ = [
    "AutonomousEcosystem",
    "DigitalTwin",
    "GovernanceProtocol",
    "ResourceMarket",
    "ResourceTrade",
]
