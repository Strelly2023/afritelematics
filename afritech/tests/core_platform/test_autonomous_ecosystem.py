from __future__ import annotations

from afritech.core_platform.autonomous_ecosystem import AutonomousEcosystem


def test_autonomous_ecosystem_produces_market_twin_and_governance_outputs() -> None:
    ecosystem = AutonomousEcosystem()

    result = ecosystem.evaluate(
        features={
            "latency_ms": 180,
            "cost_pressure": 0.4,
            "region_load": 1.3,
            "errors": 2,
            "sla_current": 100,
            "risk_score": 0.45,
            "anomaly": True,
        },
        action_bundle={
            "policy": {"action": "decrease_limit"},
            "routing": {"action": "reroute_region"},
            "cost": {"action": "reduce_cost"},
            "risk": {"action": "throttle"},
            "guardrails": {"hard_cap": 100, "min_cap": 10},
        },
        base_score=0.25,
    )

    assert result["score"] > 0
    assert result["market"]["mode"] == "simulated_exchange"
    assert result["digital_twin"]["mode"] == "projection_only"
    assert result["governance"]["mode"] == "self_evolving_guarded"
    assert result["governance"]["policy"]["max_requests"] >= 10


def test_governance_evolves_once_then_epoch_locks() -> None:
    ecosystem = AutonomousEcosystem()

    first = ecosystem.evaluate(
        features={
            "latency_ms": 50,
            "cost_pressure": 0.2,
            "region_load": 0.5,
            "errors": 0,
            "sla_current": 100,
            "risk_score": 0.1,
            "anomaly": False,
        },
        action_bundle={
            "policy": {"action": "maintain"},
            "routing": {"action": "keep_region"},
            "cost": {"action": "hold_cost"},
            "risk": {"action": "hold"},
            "guardrails": {"hard_cap": 100, "min_cap": 10},
        },
        base_score=0.25,
    )
    second = ecosystem.evaluate(
        features={
            "latency_ms": 50,
            "cost_pressure": 0.2,
            "region_load": 0.5,
            "errors": 0,
            "sla_current": 100,
            "risk_score": 0.1,
            "anomaly": False,
        },
        action_bundle={
            "policy": {"action": "maintain"},
            "routing": {"action": "keep_region"},
            "cost": {"action": "hold_cost"},
            "risk": {"action": "hold"},
            "guardrails": {"hard_cap": 100, "min_cap": 10},
        },
        base_score=0.25,
    )

    assert first["governance"]["policy"]["policy_epoch"] == second["governance"]["policy"]["policy_epoch"]
    assert second["governance"]["reason"] == "epoch_locked"
