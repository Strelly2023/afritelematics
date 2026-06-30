from __future__ import annotations

from afritech.core_platform.autonomous_control import AutonomousControlPlane


class MemoryRedis:
    def __init__(self) -> None:
        self.strings: dict[str, str] = {}

    def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ARG002
        self.strings[key] = value

    def get(self, key: str):
        return self.strings.get(key)


def test_autonomous_control_plane_recommends_actions_and_learns() -> None:
    plane = AutonomousControlPlane(client=MemoryRedis())

    recommendation = plane.recommend(
        {
            "org_id": "org-ai",
            "trust_level": "enterprise",
            "region": "AU",
            "failover_region": "EU",
            "predicted_requests_per_min": 180,
            "latency_ms": 220,
            "errors": 2,
            "region_load": 1.3,
            "sla_current": 100,
            "cost_pressure": 0.4,
            "anomaly": True,
            "hard_cap": 100,
            "min_cap": 10,
        }
    )

    assert recommendation["policy"]["action"] in {"decrease_limit", "maintain"}
    assert recommendation["routing"]["suggested_region"] in {"AU", "EU"}
    assert 0.5 <= recommendation["limit_multiplier"] <= 1.2

    observed = plane.observe(
        {
            "org_id": "org-ai",
            "trust_level": "enterprise",
            "region": "AU",
            "failover_region": "EU",
            "predicted_requests_per_min": 180,
            "latency_ms": 220,
            "errors": 2,
            "region_load": 1.3,
            "sla_current": 100,
            "cost_pressure": 0.4,
            "anomaly": True,
            "hard_cap": 100,
            "min_cap": 10,
        },
        recommendation,
    )

    assert observed["reward"] <= 1.0
    assert "policy" in observed
    assert "routing" in observed


def test_autonomous_control_plane_decides_via_simulation() -> None:
    plane = AutonomousControlPlane(client=MemoryRedis())

    decision = plane.decide(
        {
            "org_id": "org-ai",
            "trust_level": "enterprise",
            "region": "AU",
            "failover_region": "EU",
            "predicted_requests_per_min": 40,
            "latency_ms": 35,
            "errors": 0,
            "region_load": 0.45,
            "sla_current": 100,
            "cost_pressure": 0.1,
            "anomaly": False,
            "hard_cap": 100,
            "min_cap": 10,
        }
    )

    assert "simulation" in decision
    assert len(decision["simulation"]["evaluated"]) >= 3
    assert decision["simulation"]["winner_score"] == max(item["score"] for item in decision["simulation"]["evaluated"])
