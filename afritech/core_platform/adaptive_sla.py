"""AI-assisted adaptive SLA control for traffic prediction and limit tuning.

This is intentionally lightweight and deterministic: a rolling-window traffic
estimate, an exponential moving average, and a small online adaptation loop.
It is designed to be safe in production before any heavier ML stack is added.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any, Mapping
import json
import time

from afritech.core_platform.geo_routing import adjust_sla_capacity
from afritech.core_platform.autonomous_control import AutonomousControlPlane


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


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


@dataclass
class TrafficPredictor:
    """Simple EMA + trend predictor for per-org traffic."""

    alpha: float = 0.30
    trend_alpha: float = 0.15
    ema: float | None = None
    trend: float = 0.0
    samples: int = 0

    def update(self, observed_requests_per_min: float) -> float:
        observed = max(0.0, float(observed_requests_per_min))
        if self.ema is None:
            self.ema = observed
            self.trend = 0.0
        else:
            previous = self.ema
            self.ema = self.alpha * observed + (1.0 - self.alpha) * self.ema
            self.trend = self.trend_alpha * (self.ema - previous) + (1.0 - self.trend_alpha) * self.trend
        self.samples += 1
        return self.predict()

    def predict(self) -> float:
        if self.ema is None:
            return 0.0
        return max(0.0, float(self.ema) + float(self.trend))

    def adjust_learning_rate(self, *, error_ratio: float) -> None:
        error = _clamp(error_ratio, 0.0, 2.0)
        if error > 0.35:
            self.alpha = _clamp(self.alpha + 0.05, 0.10, 0.50)
        else:
            self.alpha = _clamp(self.alpha - 0.01, 0.10, 0.50)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "alpha": round(float(self.alpha), 4),
            "trend_alpha": round(float(self.trend_alpha), 4),
            "ema": None if self.ema is None else round(float(self.ema), 4),
            "trend": round(float(self.trend), 4),
            "samples": int(self.samples),
            "predicted_requests_per_min": round(float(self.predict()), 4),
        }


@dataclass
class AdaptiveSLAState:
    org_id: str
    trust_level: str
    region: str
    mode: str
    predictor: TrafficPredictor = field(default_factory=TrafficPredictor)
    window_started_at: float = field(default_factory=time.time)
    window_request_count: int = 0
    window_error_count: int = 0
    last_observed_at: float | None = None
    last_latency_ms: int | None = None
    smoothed_latency_ms: float | None = None
    last_actual_requests_per_min: float | None = None
    last_predicted_requests_per_min: float | None = None
    adjusted_limit: int | None = None
    confidence: float = 0.5
    anomaly: bool = False
    action: str = "hold"
    reason: str = "cold_start"
    policy_action: str = "maintain"
    policy_value: float = 0.0
    policy_reason: str = "rule_based"
    policy_region: str | None = None
    economic_market: dict[str, Any] | None = None
    digital_twin: dict[str, Any] | None = None
    governance: dict[str, Any] | None = None
    explainability: dict[str, Any] | None = None
    execution_score: float | None = None
    learning_reward: float | None = None
    updated_at: str = field(default_factory=_utcnow)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "org_id": self.org_id,
            "trust_level": self.trust_level,
            "region": self.region,
            "mode": self.mode,
            "window": {
                "started_at": self.window_started_at,
                "request_count": self.window_request_count,
                "error_count": self.window_error_count,
                "last_observed_at": self.last_observed_at,
            },
            "predictor": self.predictor.canonical_dict(),
            "last_latency_ms": self.last_latency_ms,
            "smoothed_latency_ms": self.smoothed_latency_ms,
            "last_actual_requests_per_min": self.last_actual_requests_per_min,
            "last_predicted_requests_per_min": self.last_predicted_requests_per_min,
            "adjusted_limit": self.adjusted_limit,
            "confidence": round(float(self.confidence), 4),
            "anomaly": self.anomaly,
            "action": self.action,
            "reason": self.reason,
            "policy_action": self.policy_action,
            "policy_value": round(float(self.policy_value), 4),
            "policy_reason": self.policy_reason,
            "policy_region": self.policy_region,
            "economic_market": self.economic_market,
            "digital_twin": self.digital_twin,
            "governance": self.governance,
            "explainability": self.explainability,
            "execution_score": self.execution_score,
            "learning_reward": self.learning_reward,
            "updated_at": self.updated_at,
        }


def _present_state(state: AdaptiveSLAState) -> dict[str, Any]:
    payload = state.canonical_dict()
    predicted = state.last_predicted_requests_per_min
    if predicted is None:
        predicted = state.predictor.predict() or 0.0
    payload["prediction"] = {
        "predicted_requests_per_min": round(float(predicted), 4),
        "confidence": round(float(state.confidence), 4),
        "mode": state.mode,
        "region": state.region,
    }
    payload["policy"] = {
        "adjusted_limit": int(state.adjusted_limit or 0),
        "reason": state.reason,
        "action": state.action,
        "anomaly": state.anomaly,
    }
    payload["autonomy"] = {
        "action": state.policy_action,
        "value": round(float(state.policy_value), 4),
        "reason": state.policy_reason,
        "region": state.policy_region or state.region,
        "economy": state.economic_market or {},
        "digital_twin": state.digital_twin or {},
        "governance": state.governance or {},
        "explainability": state.explainability or {},
        "execution_score": None if state.execution_score is None else round(float(state.execution_score), 4),
        "learning_reward": None if state.learning_reward is None else round(float(state.learning_reward), 4),
    }
    return payload


def adaptive_sla_limit(
    base_limit: int,
    predicted_requests_per_min: float,
    trust_level: str,
    *,
    latency_ms: int | None = None,
    anomaly: bool = False,
) -> tuple[int, str]:
    base = max(1, int(base_limit))
    predicted = max(0.0, float(predicted_requests_per_min))
    trust = str(trust_level or "").strip().lower() or "sandbox"

    if trust == "regulator":
        return base, "regulatory_override"
    if trust == "sandbox":
        limit = base
        reason = "static_sandbox_sla"
    elif predicted < base * 0.7:
        limit = int(round(base * 1.2))
        reason = "burst_room_for_expected_headroom"
    elif predicted < base:
        limit = base
        reason = "steady_state_capacity"
    elif predicted < base * 1.5:
        limit = int(round(base * 0.8))
        reason = "predicted_growth_contraction"
    else:
        limit = int(round(base * 0.5))
        reason = "protective_contraction"

    if latency_ms is not None:
        latency_adjusted = adjust_sla_capacity(limit, latency_ms, trust)
        limit = min(limit, latency_adjusted)

    if anomaly:
        limit = max(1, int(round(limit * 0.5)))
        reason = f"anomaly_{reason}"

    return max(1, int(limit)), reason


class AdaptiveSLAController:
    """Persisted adaptive SLA controller with rolling predictions."""

    def __init__(
        self,
        client: Any,
        *,
        key_prefix: str = "ai:adaptive_sla",
        region: str = "AU",
        default_limit: int = 1_000,
        autonomous_control: AutonomousControlPlane | None = None,
    ) -> None:
        self.client = client
        self.key_prefix = key_prefix
        self.region = str(region or "AU").upper()
        self.default_limit = max(1, int(default_limit))
        self.autonomous_control = autonomous_control

    def _state_key(self, org_id: str) -> str:
        return f"{self.key_prefix}:{org_id}"

    def _load_state(self, org_id: str) -> AdaptiveSLAState | None:
        payload = _safe_json_loads(self.client.get(self._state_key(org_id)))
        if not payload:
            return None
        predictor_payload = payload.get("predictor") or {}
        predictor = TrafficPredictor(
            alpha=_clamp(_safe_float(predictor_payload.get("alpha"), 0.30), 0.10, 0.50),
            trend_alpha=_clamp(_safe_float(predictor_payload.get("trend_alpha"), 0.15), 0.05, 0.30),
            ema=None if predictor_payload.get("ema") is None else _safe_float(predictor_payload.get("ema")),
            trend=_safe_float(predictor_payload.get("trend")),
            samples=_safe_int(predictor_payload.get("samples")),
        )
        window = payload.get("window") or {}
        return AdaptiveSLAState(
            org_id=str(payload.get("org_id") or org_id),
            trust_level=str(payload.get("trust_level") or "sandbox"),
            region=str(payload.get("region") or self.region).upper(),
            mode=str(payload.get("mode") or "cold_start"),
            predictor=predictor,
            window_started_at=_safe_float(window.get("started_at"), time.time()),
            window_request_count=_safe_int(window.get("request_count")),
            window_error_count=_safe_int(window.get("error_count")),
            last_observed_at=window.get("last_observed_at"),
            last_latency_ms=None if payload.get("last_latency_ms") is None else _safe_int(payload.get("last_latency_ms")),
            smoothed_latency_ms=None if payload.get("smoothed_latency_ms") is None else _safe_float(payload.get("smoothed_latency_ms")),
            last_actual_requests_per_min=payload.get("last_actual_requests_per_min"),
            last_predicted_requests_per_min=payload.get("last_predicted_requests_per_min"),
            adjusted_limit=None if payload.get("adjusted_limit") is None else _safe_int(payload.get("adjusted_limit")),
            confidence=_clamp(_safe_float(payload.get("confidence"), 0.5), 0.0, 1.0),
            anomaly=bool(payload.get("anomaly", False)),
            action=str(payload.get("action") or "hold"),
            reason=str(payload.get("reason") or "cold_start"),
            policy_action=str(payload.get("policy_action") or "maintain"),
            policy_value=_safe_float(payload.get("policy_value"), 0.0),
            policy_reason=str(payload.get("policy_reason") or "rule_based"),
            policy_region=None if payload.get("policy_region") is None else str(payload.get("policy_region")).upper(),
            economic_market=None if payload.get("economic_market") is None else dict(payload.get("economic_market") or {}),
            digital_twin=None if payload.get("digital_twin") is None else dict(payload.get("digital_twin") or {}),
            governance=None if payload.get("governance") is None else dict(payload.get("governance") or {}),
            explainability=None if payload.get("explainability") is None else dict(payload.get("explainability") or {}),
            execution_score=None if payload.get("execution_score") is None else _safe_float(payload.get("execution_score")),
            learning_reward=None if payload.get("learning_reward") is None else _safe_float(payload.get("learning_reward")),
            updated_at=str(payload.get("updated_at") or _utcnow()),
        )

    def _save_state(self, state: AdaptiveSLAState) -> AdaptiveSLAState:
        self.client.set(self._state_key(state.org_id), json.dumps(state.canonical_dict(), sort_keys=True, separators=(",", ":")), ex=24 * 60 * 60)
        return state

    def _smoothed_latency_ms(self, state: AdaptiveSLAState, latency_ms: int | None) -> int | None:
        if latency_ms is None:
            return None
        observed = max(0.0, float(latency_ms))
        if state.smoothed_latency_ms is None:
            return int(round(observed))
        smoothed = 0.7 * float(state.smoothed_latency_ms) + 0.3 * observed
        return int(round(smoothed))

    def snapshot(self, org_id: str) -> dict[str, Any]:
        state = self._load_state(org_id)
        if state is None:
            return {
                "org_id": org_id,
                "region": self.region,
                "mode": "cold_start",
                "prediction": {
                    "predicted_requests_per_min": float(self.default_limit),
                    "confidence": 0.0,
                    "mode": "cold_start",
                    "region": self.region,
                },
                "policy": {
                    "adjusted_limit": self.default_limit,
                    "reason": "no_observations_yet",
                    "action": "hold",
                    "anomaly": False,
                },
                "anomaly": False,
                "action": "hold",
                "smoothed_latency_ms": None,
                "autonomy": {
                    "action": "maintain",
                    "value": 0.0,
                    "reason": "no_observations_yet",
                    "region": self.region,
                },
            }
        return _present_state(state)

    def recommend(
        self,
        org_id: str,
        *,
        trust_level: str,
        base_limit: int,
        region: str | None = None,
        latency_ms: int | None = None,
        health_map: Mapping[str, Any] | None = None,  # noqa: ARG002 - reserved for future regional weighting
        load_hint: float | None = None,
    ) -> dict[str, Any]:
        state = self._load_state(org_id) or AdaptiveSLAState(
            org_id=org_id,
            trust_level=str(trust_level or "sandbox"),
            region=str(region or self.region).upper(),
            mode="cold_start",
            predictor=TrafficPredictor(),
            adjusted_limit=max(1, int(base_limit)),
        )
        trust = str(trust_level or state.trust_level).strip().lower() or "sandbox"
        observed_hint = load_hint if load_hint is not None else state.last_actual_requests_per_min
        predicted = state.predictor.predict()
        if state.predictor.samples == 0:
            predicted = float(base_limit)
        elif observed_hint is not None:
            predicted = max(predicted, float(observed_hint))

        anomaly = bool(state.anomaly)
        smoothed_latency = self._smoothed_latency_ms(state, latency_ms)
        healthy_regions = [region_name for region_name in ("AU", "EU", "US") if str((health_map or {}).get(region_name, "healthy")).strip().lower() not in {"down", "degraded", "unhealthy", "disabled", "critical"}]
        failover_region = next((region_name for region_name in healthy_regions if region_name != str(region or state.region).upper()), None)
        if trust == "regulator" or state.predictor.samples < 3:
            adjusted_limit = int(base_limit)
            reason = "regulatory_override" if trust == "regulator" else "cold_start_stable_limit"
        else:
            adjusted_limit, reason = adaptive_sla_limit(
                base_limit,
                predicted,
                trust_level,
                latency_ms=smoothed_latency,
                anomaly=anomaly,
            )
        if trust == "sandbox":
            mode = "static"
        elif trust in {"verified", "enterprise", "regulator"}:
            mode = "predictive"
        else:
            mode = "adaptive"
        if observed_hint is None or state.predictor.samples < 3:
            confidence = 0.05
        else:
            error_ratio = abs(float(predicted) - float(observed_hint)) / max(1.0, float(observed_hint))
            confidence = _clamp(1.0 - error_ratio, 0.05, 0.99)
        policy_action = "maintain"
        policy_value = 0.0
        policy_reason = "rule_based"
        policy_region = str(region or state.region).upper()
        economic_market: dict[str, Any] | None = state.economic_market
        digital_twin: dict[str, Any] | None = state.digital_twin
        governance: dict[str, Any] | None = state.governance
        explainability: dict[str, Any] | None = state.explainability
        execution_score: float | None = state.execution_score
        learning_reward: float | None = state.learning_reward
        apply_autonomy = self.autonomous_control is not None and trust != "regulator" and state.predictor.samples >= 3
        if self.autonomous_control is not None:
            autonomy = self.autonomous_control.recommend(
                {
                    "org_id": org_id,
                    "trust_level": trust_level,
                    "region": str(region or state.region).upper(),
                    "failover_region": failover_region,
                    "predicted_requests_per_min": predicted,
                    "latency_ms": smoothed_latency,
                    "errors": 1 if anomaly else 0,
                    "region_load": float(adjusted_limit) / max(1.0, float(base_limit)),
                    "sla_current": base_limit,
                    "cost_pressure": max(0.0, float(base_limit - adjusted_limit) / max(1.0, float(base_limit))),
                    "anomaly": anomaly,
                    "hard_cap": max(1, int(base_limit)),
                    "min_cap": 1,
                }
            )
            policy_action = str((autonomy.get("policy") or {}).get("action") or "maintain")
            policy_value = _safe_float((autonomy.get("policy") or {}).get("value"), 0.0)
            policy_reason = "autonomous_applied" if apply_autonomy else "cold_start_guardrail"
            policy_region = str((autonomy.get("routing") or {}).get("suggested_region") or policy_region).upper()
            economic_market = dict(autonomy.get("economy") or {})
            digital_twin = dict(autonomy.get("digital_twin") or {})
            governance = dict(autonomy.get("governance") or {})
            explainability = dict(autonomy.get("explainability") or {})
            execution_score = _safe_float(autonomy.get("execution_score"), execution_score if execution_score is not None else 0.0)
            learning_reward = _safe_float(autonomy.get("learning_reward"), learning_reward if learning_reward is not None else 0.0)
            multiplier = _safe_float(autonomy.get("limit_multiplier"), 1.0) if apply_autonomy else 1.0
            adjusted_limit = max(1, int(round(float(adjusted_limit) * multiplier)))
            if apply_autonomy and policy_action == "reroute_region" and policy_region:
                region = policy_region
        recommendation = replace(
            state,
            trust_level=str(trust_level or state.trust_level),
            region=str(region or state.region).upper(),
            mode=mode,
            last_latency_ms=latency_ms,
            smoothed_latency_ms=smoothed_latency,
            last_predicted_requests_per_min=round(float(predicted), 4),
            adjusted_limit=int(adjusted_limit),
            confidence=confidence,
            anomaly=anomaly,
            action="throttle" if anomaly or adjusted_limit < int(base_limit) else "expand" if adjusted_limit > int(base_limit) else "hold",
            reason=reason,
            policy_action=policy_action,
            policy_value=policy_value,
            policy_reason=policy_reason,
            policy_region=policy_region,
            economic_market=economic_market,
            digital_twin=digital_twin,
            governance=governance,
            explainability=explainability,
            execution_score=execution_score,
            learning_reward=learning_reward,
            updated_at=_utcnow(),
        )
        self._save_state(recommendation)
        return _present_state(recommendation)

    def observe(
        self,
        org_id: str,
        *,
        trust_level: str,
        base_limit: int,
        region: str | None = None,
        latency_ms: int | None = None,
        errors: int = 0,
        observed_at: float | None = None,
    ) -> dict[str, Any]:
        now = float(observed_at if observed_at is not None else time.time())
        state = self._load_state(org_id) or AdaptiveSLAState(
            org_id=org_id,
            trust_level=str(trust_level or "sandbox"),
            region=str(region or self.region).upper(),
            mode="cold_start",
            predictor=TrafficPredictor(),
            adjusted_limit=max(1, int(base_limit)),
        )

        window_started = float(state.window_started_at or now)
        elapsed = max(5.0, now - window_started) if now >= window_started else 5.0
        if now - window_started >= 60.0:
            state.window_started_at = now
            state.window_request_count = 0
            state.window_error_count = 0
            elapsed = 5.0

        state.window_request_count += 1
        state.window_error_count += max(0, int(errors))
        state.last_observed_at = now
        actual_requests_per_min = (float(state.window_request_count) * 60.0) / elapsed
        predicted = state.predictor.update(actual_requests_per_min)
        error_ratio = abs(actual_requests_per_min - predicted) / max(1.0, predicted)
        state.predictor.adjust_learning_rate(error_ratio=error_ratio)

        anomaly = bool(errors) or actual_requests_per_min > predicted * 2.0
        trust = str(trust_level or state.trust_level).strip().lower() or "sandbox"
        smoothed_latency = self._smoothed_latency_ms(state, latency_ms)
        adjusted_limit, reason = adaptive_sla_limit(
            base_limit,
            predicted,
            trust_level,
            latency_ms=smoothed_latency,
            anomaly=anomaly,
        )
        confidence = _clamp(1.0 - error_ratio, 0.05, 0.99)
        mode = "static" if trust == "sandbox" else "predictive"
        policy_action = state.policy_action
        policy_value = state.policy_value
        policy_reason = state.policy_reason
        policy_region = state.policy_region or str(region or state.region).upper()
        economic_market = state.economic_market
        digital_twin = state.digital_twin
        governance = state.governance
        explainability = state.explainability
        execution_score = state.execution_score
        learning_reward = state.learning_reward
        if self.autonomous_control is not None:
            autonomous = self.autonomous_control.observe(
                {
                    "org_id": org_id,
                    "trust_level": trust_level,
                    "region": str(region or state.region).upper(),
                    "failover_region": None,
                    "predicted_requests_per_min": predicted,
                    "latency_ms": smoothed_latency,
                    "errors": errors,
                    "region_load": float(adjusted_limit) / max(1.0, float(base_limit)),
                    "sla_current": base_limit,
                    "cost_pressure": max(0.0, float(base_limit - adjusted_limit) / max(1.0, float(base_limit))),
                    "anomaly": anomaly,
                    "hard_cap": max(1, int(base_limit)),
                    "min_cap": 1,
                },
                {
                    "policy": {
                        "action": state.policy_action,
                        "value": state.policy_value,
                    },
                    "routing": {
                        "action": "reroute_region" if state.policy_region and state.policy_region != state.region else "keep_region",
                        "suggested_region": state.policy_region or state.region,
                    },
                    "cost": {
                        "action": "hold_cost",
                    },
                    "risk": {
                        "action": "throttle" if anomaly else "hold",
                    },
                },
            )
            policy_action = str((autonomous.get("policy") or {}).get("action") or policy_action)
            policy_value = _safe_float((autonomous.get("policy") or {}).get("value"), policy_value)
            policy_reason = f"reward:{_safe_float(autonomous.get('reward'), 0.0):.4f}"
            policy_region = str((autonomous.get("routing") or {}).get("suggested_region") or policy_region).upper()
            economic_market = dict(autonomous.get("economy") or economic_market or {})
            digital_twin = dict(autonomous.get("digital_twin") or digital_twin or {})
            governance = dict(autonomous.get("governance") or governance or {})
            explainability = dict(autonomous.get("explainability") or explainability or {})
            execution_score = _safe_float(autonomous.get("execution_score"), execution_score if execution_score is not None else 0.0)
            learning_reward = _safe_float(autonomous.get("learning_reward"), learning_reward if learning_reward is not None else 0.0)
        updated = replace(
            state,
            trust_level=str(trust_level or state.trust_level),
            region=str(region or state.region).upper(),
            mode=mode,
            last_latency_ms=latency_ms,
            smoothed_latency_ms=smoothed_latency,
            last_actual_requests_per_min=round(float(actual_requests_per_min), 4),
            last_predicted_requests_per_min=round(float(predicted), 4),
            adjusted_limit=int(adjusted_limit),
            confidence=confidence,
            anomaly=anomaly,
            action="throttle" if anomaly or adjusted_limit < int(base_limit) else "expand" if adjusted_limit > int(base_limit) else "hold",
            reason=reason,
            policy_action=policy_action,
            policy_value=policy_value,
            policy_reason=policy_reason,
            policy_region=policy_region,
            economic_market=economic_market,
            digital_twin=digital_twin,
            governance=governance,
            explainability=explainability,
            execution_score=execution_score,
            learning_reward=learning_reward,
            updated_at=_utcnow(),
        )
        return _present_state(self._save_state(updated))


__all__ = [
    "AdaptiveSLAController",
    "AdaptiveSLAState",
    "TrafficPredictor",
    "adaptive_sla_limit",
]
