"""Bounded autonomous control layer for SLA, routing, risk, and cost hints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import hashlib
import json


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_json_loads(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8")
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return {}
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}
    if isinstance(raw, Mapping):
        return dict(raw)
    return {}


def _state_signature(features: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(_canonical_json(dict(features))).hexdigest()
    return digest[:24]


@dataclass
class AutonomousPolicyAgent:
    client: Any
    key_prefix: str
    actions: tuple[str, ...]
    learning_rate: float = 0.25

    def _state_key(self, features: Mapping[str, Any]) -> str:
        return f"{self.key_prefix}:{_state_signature(features)}"

    def _load_values(self, features: Mapping[str, Any]) -> dict[str, float]:
        payload = _safe_json_loads(self.client.get(self._state_key(features)))
        values: dict[str, float] = {}
        for action, raw in (payload.get("values") or {}).items():
            values[str(action)] = _safe_float(raw)
        return values

    def _save_values(self, features: Mapping[str, Any], values: Mapping[str, float]) -> None:
        payload = {"values": {str(action): round(_safe_float(value), 4) for action, value in values.items()}}
        self.client.set(self._state_key(features), json.dumps(payload, sort_keys=True, separators=(",", ":")), ex=7 * 24 * 60 * 60)

    def propose(self, features: Mapping[str, Any], *, fallback: str) -> dict[str, Any]:
        values = self._load_values(features)
        ranked = sorted(
            self.actions,
            key=lambda action: (values.get(action, 0.0), -self.actions.index(action)),
            reverse=True,
        )
        if not ranked:
            action = fallback
        else:
            learned = values.get(ranked[0], 0.0)
            action = ranked[0] if learned != 0.0 else fallback
        return {
            "action": action,
            "value": round(values.get(action, 0.0), 4),
            "learned": {action_name: round(values.get(action_name, 0.0), 4) for action_name in self.actions},
        }

    def update(self, features: Mapping[str, Any], action: str, reward: float) -> dict[str, Any]:
        values = self._load_values(features)
        previous = _safe_float(values.get(action, 0.0))
        updated = previous + self.learning_rate * (_safe_float(reward) - previous)
        values[action] = updated
        self._save_values(features, values)
        return {
            "action": action,
            "value": round(updated, 4),
            "learned": {action_name: round(values.get(action_name, 0.0), 4) for action_name in self.actions},
        }


class AutonomousControlPlane:
    """Small deterministic multi-agent control plane with Q-like updates."""

    def __init__(self, client: Any, *, key_prefix: str = "ai:autonomy") -> None:
        self.client = client
        self.key_prefix = key_prefix
        self.sla_agent = AutonomousPolicyAgent(
            client,
            key_prefix=f"{key_prefix}:sla",
            actions=("increase_limit", "maintain", "decrease_limit"),
        )
        self.routing_agent = AutonomousPolicyAgent(
            client,
            key_prefix=f"{key_prefix}:routing",
            actions=("reroute_region", "keep_region"),
        )
        self.cost_agent = AutonomousPolicyAgent(
            client,
            key_prefix=f"{key_prefix}:cost",
            actions=("reduce_cost", "hold_cost", "scale_cost"),
        )
        self.risk_agent = AutonomousPolicyAgent(
            client,
            key_prefix=f"{key_prefix}:risk",
            actions=("throttle", "hold", "escalate"),
        )

    @staticmethod
    def _limit_multiplier(action: str) -> float:
        return {
            "increase_limit": 1.10,
            "decrease_limit": 0.85,
            "maintain": 1.0,
            "reduce_cost": 0.92,
            "hold_cost": 1.0,
            "scale_cost": 1.05,
            "throttle": 0.50,
            "hold": 1.0,
            "escalate": 0.75,
        }.get(action, 1.0)

    @staticmethod
    def _derive_reward(features: Mapping[str, Any], action_bundle: Mapping[str, Any]) -> float:
        latency_ms = _safe_float(features.get("latency_ms"))
        errors = _safe_float(features.get("errors"))
        predicted = max(1.0, _safe_float(features.get("predicted_requests_per_min"), _safe_float(features.get("sla_current"), 1.0)))
        current_limit = max(1.0, _safe_float(features.get("sla_current"), predicted))
        cost_pressure = _safe_float(features.get("cost_pressure"))
        anomaly = bool(features.get("anomaly", False))

        success_score = 1.0
        error_penalty = min(2.0, errors * 0.4)
        latency_penalty = min(1.5, max(0.0, (latency_ms - 80.0) / 160.0))
        cost_penalty = min(1.0, max(0.0, cost_pressure))
        over_provision_penalty = min(1.0, max(0.0, (current_limit - predicted) / predicted))

        reward = success_score - error_penalty - latency_penalty - cost_penalty - (0.5 if anomaly else 0.0) - 0.25 * over_provision_penalty
        return round(reward, 4)

    def recommend(self, features: Mapping[str, Any]) -> dict[str, Any]:
        latency_ms = _safe_float(features.get("latency_ms"))
        errors = _safe_float(features.get("errors"))
        predicted = _safe_float(features.get("predicted_requests_per_min"))
        current_limit = max(1.0, _safe_float(features.get("sla_current"), predicted or 1.0))
        region_load = _safe_float(features.get("region_load"))
        cost_pressure = _safe_float(features.get("cost_pressure"))
        anomaly = bool(features.get("anomaly", False))
        failover_region = str(features.get("failover_region") or "").strip().upper()

        if anomaly or errors > 0 or latency_ms > 150:
            sla_fallback = "decrease_limit"
            risk_fallback = "throttle"
        elif predicted and predicted < current_limit * 0.7 and latency_ms < 100:
            sla_fallback = "increase_limit"
            risk_fallback = "hold"
        else:
            sla_fallback = "maintain"
            risk_fallback = "hold"

        if failover_region and (latency_ms > 150 or errors > 0 or region_load > 1.0):
            routing_fallback = "reroute_region"
        else:
            routing_fallback = "keep_region"

        if cost_pressure > 0.15 and latency_ms < 150:
            cost_fallback = "reduce_cost"
        else:
            cost_fallback = "hold_cost"

        sla = self.sla_agent.propose(features, fallback=sla_fallback)
        routing = self.routing_agent.propose(features, fallback=routing_fallback)
        cost = self.cost_agent.propose(features, fallback=cost_fallback)
        risk = self.risk_agent.propose(features, fallback=risk_fallback)

        multiplier = 1.0
        for action in (sla["action"], cost["action"], risk["action"]):
            multiplier *= self._limit_multiplier(action)
        if routing["action"] == "reroute_region":
            multiplier *= 0.98

        multiplier = _clamp(multiplier, 0.5, 1.2)
        suggested_region = str(features.get("failover_region") or features.get("region") or "").upper() or None
        if routing["action"] != "reroute_region":
            suggested_region = str(features.get("region") or "").upper() or None

        return {
            "policy": sla,
            "routing": {
                **routing,
                "suggested_region": suggested_region,
            },
            "cost": cost,
            "risk": risk,
            "limit_multiplier": round(multiplier, 4),
            "guardrails": {
                "min_multiplier": 0.5,
                "max_multiplier": 1.2,
                "hard_cap": _safe_int(features.get("hard_cap"), 10_000),
                "min_cap": _safe_int(features.get("min_cap"), 1),
            },
        }

    def observe(self, features: Mapping[str, Any], recommendation: Mapping[str, Any]) -> dict[str, Any]:
        reward = self._derive_reward(features, recommendation)
        policy = recommendation.get("policy") or {}
        routing = recommendation.get("routing") or {}
        cost = recommendation.get("cost") or {}
        risk = recommendation.get("risk") or {}
        state = {
            "traffic": round(_safe_float(features.get("predicted_requests_per_min")), 4),
            "latency": round(_safe_float(features.get("latency_ms")), 4),
            "errors": round(_safe_float(features.get("errors")), 4),
            "region_load": round(_safe_float(features.get("region_load")), 4),
            "sla_current": round(_safe_float(features.get("sla_current")), 4),
            "cost_pressure": round(_safe_float(features.get("cost_pressure")), 4),
            "anomaly": bool(features.get("anomaly", False)),
            "region": str(features.get("region") or "").upper(),
            "failover_region": str(features.get("failover_region") or "").upper(),
        }
        updated_policy = self.sla_agent.update(state, str(policy.get("action") or "maintain"), reward)
        updated_routing = self.routing_agent.update(state, str(routing.get("action") or "keep_region"), reward)
        updated_cost = self.cost_agent.update(state, str(cost.get("action") or "hold_cost"), reward)
        updated_risk = self.risk_agent.update(state, str(risk.get("action") or "hold"), reward)
        return {
            "reward": reward,
            "state": state,
            "policy": updated_policy,
            "routing": updated_routing,
            "cost": updated_cost,
            "risk": updated_risk,
        }


__all__ = ["AutonomousControlPlane", "AutonomousPolicyAgent"]
