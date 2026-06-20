from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean, pstdev
from typing import Any

from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class TrustTrendService:
    def __init__(self, repository: PlatformStore | None = None) -> None:
        self.repository = repository or get_platform_store()

    def compute(self, organization_id: str) -> dict[str, Any]:
        history = self.repository.list_trust_scores(organization_id=organization_id, limit=365)
        scores = list(reversed(history))
        values = [int(item["trust_score"]) for item in scores]
        if not values:
            values = [0]
            scores = []
        current = values[-1]
        by_age: dict[int, list[int]] = defaultdict(list)
        now = _parse_time(scores[-1]["computed_at"]) if scores else datetime.utcnow()
        for item in scores:
            age_days = max(0, (now - _parse_time(item["computed_at"])).days)
            by_age[min(age_days, 90)].append(int(item["trust_score"]))
        def avg_for(days: int) -> float:
            window = [score for idx, item in enumerate(scores) if max(0, (now - _parse_time(item["computed_at"])).days) <= days for score in [int(item["trust_score"])]]
            return round(mean(window), 2) if window else float(current)
        avg7 = avg_for(7)
        avg30 = avg_for(30)
        avg90 = avg_for(90)
        volatility = pstdev(values) if len(values) > 1 else 0.0
        direction = "stable"
        if current > avg7 + 1:
            direction = "improving"
        elif current < avg7 - 1:
            direction = "degrading"
        if volatility >= 12:
            direction = "volatile"
        if current < 45:
            direction = "critical"
        anomaly_count = len([score for score in values if abs(score - avg30) >= max(8, volatility * 1.5)])
        recovery_rate = 0.0
        if len(values) >= 2 and values[0] < values[-1]:
            recovery_rate = round(((values[-1] - min(values)) / max(1, 100 - min(values))) * 100, 2)
        risk_score = max(0, 100 - current + anomaly_count)
        return {
            "organization_id": organization_id,
            "current_score": current,
            "7_day_average": avg7,
            "30_day_average": avg30,
            "90_day_average": avg90,
            "volatility": round(volatility, 2),
            "direction": direction,
            "recovery_rate": recovery_rate,
            "anomaly_count": anomaly_count,
            "risk_score": risk_score,
        }
