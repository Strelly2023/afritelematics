"""Explainable weighted dispatch and operational intelligence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from statistics import fmean
from typing import Any


DEFAULT_WEIGHTS = {
    "distance": 0.16,
    "traffic": 0.10,
    "driver_rating": 0.10,
    "vehicle_type": 0.08,
    "acceptance_rate": 0.10,
    "trust_score": 0.16,
    "battery_level": 0.06,
    "estimated_arrival": 0.16,
    "surge_demand": 0.08,
}


@dataclass(frozen=True)
class DispatchCandidate:
    driver_id: str
    distance_km: float
    traffic_factor: float
    driver_rating: float
    vehicle_type: str
    acceptance_rate: float
    trust_score: float
    battery_level: float
    estimated_arrival_minutes: float
    surge_demand: float
    online: bool = True
    device_trusted: bool = True
    open_safety_incidents: int = 0
    fraud_risk_score: float = 0.0


@dataclass(frozen=True)
class DispatchPolicy:
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    minimum_trust_score: float = 60
    minimum_battery_level: float = 10
    maximum_fraud_risk: float = 0.7
    automatic_assignment_score: float = 0.72
    automatic_assignment_margin: float = 0.08

    def __post_init__(self) -> None:
        if set(self.weights) != set(DEFAULT_WEIGHTS):
            raise ValueError("dispatch weights must define every supported factor")
        if abs(sum(self.weights.values()) - 1.0) > 0.000001:
            raise ValueError("dispatch weights must sum to 1")
        if any(weight < 0 for weight in self.weights.values()):
            raise ValueError("dispatch weights cannot be negative")


class WeightedDispatchEngine:
    def __init__(self, policy: DispatchPolicy | None = None) -> None:
        self.policy = policy or DispatchPolicy()

    def rank(self, candidates: list[DispatchCandidate], *, requested_vehicle_type: str,
             trace_id: str) -> dict[str, Any]:
        ranked = [self._score(candidate, requested_vehicle_type) for candidate in candidates]
        ranked.sort(key=lambda row: (-row["score"], row["eta_minutes"], row["driver_id"]))
        eligible = [row for row in ranked if row["eligible"]]
        winner = eligible[0] if eligible else None
        runner_up = eligible[1] if len(eligible) > 1 else None
        margin = round(
            winner["score"] - runner_up["score"] if winner and runner_up else winner["score"] if winner else 0,
            6,
        )
        automatic = bool(
            winner
            and winner["score"] >= self.policy.automatic_assignment_score
            and margin >= self.policy.automatic_assignment_margin
        )
        return {
            "contract": "afriride.dispatch.v1",
            "trace_id": trace_id,
            "evaluated_at": datetime.now(UTC).isoformat(),
            "policy": asdict(self.policy),
            "selected_driver_id": winner["driver_id"] if winner else None,
            "selected_score": winner["score"] if winner else 0,
            "confidence_margin": margin,
            "automation": {
                "eligible": automatic,
                "mode": "automatic_policy_clear" if automatic else "operator_review",
                "reason": (
                    "score_and_margin_thresholds_passed"
                    if automatic
                    else "no_eligible_driver" if not winner else "confidence_threshold_not_met"
                ),
            },
            "candidates": ranked,
            "authority": "advisory_until_dispatcher_accepts",
        }

    def _score(self, candidate: DispatchCandidate, requested_vehicle_type: str) -> dict[str, Any]:
        factors = {
            "distance": _inverse(candidate.distance_km, 30),
            "traffic": _inverse(max(0, candidate.traffic_factor - 1) * 10, 20),
            "driver_rating": _clamp(candidate.driver_rating / 5),
            "vehicle_type": 1.0 if candidate.vehicle_type.casefold() == requested_vehicle_type.casefold() else 0.0,
            "acceptance_rate": _clamp(candidate.acceptance_rate),
            "trust_score": _clamp(candidate.trust_score / 100),
            "battery_level": _clamp(candidate.battery_level / 100),
            "estimated_arrival": _inverse(candidate.estimated_arrival_minutes, 45),
            "surge_demand": _clamp(
                (candidate.surge_demand * 0.5)
                + (candidate.acceptance_rate * 0.25)
                + (_inverse(candidate.distance_km, 30) * 0.25)
            ),
        }
        gates = {
            "online": candidate.online,
            "device_trusted": candidate.device_trusted,
            "trust": candidate.trust_score >= self.policy.minimum_trust_score,
            "battery": candidate.battery_level >= self.policy.minimum_battery_level,
            "safety": candidate.open_safety_incidents == 0,
            "fraud": candidate.fraud_risk_score <= self.policy.maximum_fraud_risk,
        }
        contributions = {
            factor: round(value * self.policy.weights[factor], 6)
            for factor, value in factors.items()
        }
        return {
            "driver_id": candidate.driver_id,
            "score": round(sum(contributions.values()), 6) if all(gates.values()) else 0,
            "eligible": all(gates.values()),
            "gates": gates,
            "factors": {key: round(value, 6) for key, value in factors.items()},
            "contributions": contributions,
            "eta_minutes": candidate.estimated_arrival_minutes,
            "exclusions": [key for key, passed in gates.items() if not passed],
        }


def fleet_analytics(candidates: list[DispatchCandidate]) -> dict[str, Any]:
    online = [candidate for candidate in candidates if candidate.online]
    return {
        "driver_count": len(candidates),
        "online_drivers": len(online),
        "average_rating": round(fmean(c.driver_rating for c in candidates), 3) if candidates else 0,
        "average_acceptance_rate": round(fmean(c.acceptance_rate for c in candidates), 4) if candidates else 0,
        "average_trust_score": round(fmean(c.trust_score for c in candidates), 2) if candidates else 0,
        "low_battery_drivers": sum(c.battery_level < 20 for c in online),
        "high_fraud_risk_drivers": sum(c.fraud_risk_score > 0.7 for c in candidates),
        "open_safety_incidents": sum(c.open_safety_incidents for c in candidates),
        "average_eta_minutes": round(fmean(c.estimated_arrival_minutes for c in online), 2) if online else 0,
    }


def operational_alerts(candidates: list[DispatchCandidate]) -> list[dict[str, Any]]:
    alerts = []
    for candidate in candidates:
        signals = []
        if candidate.battery_level < 15:
            signals.append(("warning", "driver_low_battery"))
        if candidate.trust_score < 60 or not candidate.device_trusted:
            signals.append(("critical", "driver_integrity_hold"))
        if candidate.fraud_risk_score > 0.7:
            signals.append(("critical", "fraud_risk_high"))
        if candidate.open_safety_incidents:
            signals.append(("critical", "open_safety_incident"))
        for severity, alert_type in signals:
            alerts.append({
                "alert_id": f"{alert_type}:{candidate.driver_id}",
                "alert_type": alert_type,
                "severity": severity,
                "driver_id": candidate.driver_id,
                "automation": "dispatch_excluded" if severity == "critical" else "operator_notify",
            })
    return alerts


def _inverse(value: float, ceiling: float) -> float:
    return _clamp(1 - max(0, value) / ceiling)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
