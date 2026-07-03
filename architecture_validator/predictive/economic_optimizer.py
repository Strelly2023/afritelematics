from __future__ import annotations

from typing import Any


class EconomicOptimizer:
    def optimize(self, metrics: dict[str, Any]) -> dict[str, Any]:
        cost = float(metrics.get("cost") or 0)
        budget = float(metrics.get("budget") or 0)
        latency = float(metrics.get("latency") or 0)
        demand = float(metrics.get("demand") or 0)
        failure_risk = float(metrics.get("failure_risk") or 0)

        actions: list[dict[str, str]] = []
        if budget and cost > budget:
            actions.append(
                {
                    "action": "reduce_cost",
                    "method": "scale_down_services",
                    "reason": "Cost is above budget.",
                }
            )
        if latency > 200:
            actions.append(
                {
                    "action": "increase_performance",
                    "method": "scale_up_nodes",
                    "reason": "Latency is above the governed threshold.",
                }
            )
        if demand and demand < 35:
            actions.append(
                {
                    "action": "consolidate_services",
                    "method": "merge_low_traffic_capacity",
                    "reason": "Demand is low enough to justify consolidation.",
                }
            )
        if failure_risk >= 70:
            actions.append(
                {
                    "action": "increase_redundancy",
                    "method": "add_resilience_capacity",
                    "reason": "Failure risk requires redundancy.",
                }
            )

        efficiency = 100
        if budget:
            efficiency = int(round(max(0.0, min(100.0, 100.0 - ((cost - budget) / budget * 100.0))))) if cost > budget else 100
        if latency > 0:
            efficiency = max(0, min(100, int(round(efficiency - max(0.0, (latency - 120.0) / 4.0)))))

        return {
            "budget": budget,
            "cost": cost,
            "latency": latency,
            "demand": demand,
            "failure_risk": failure_risk,
            "action": actions[0]["action"] if actions else "hold",
            "decision": actions[0] if actions else {"action": "hold", "method": "monitor", "reason": "Metrics remain within tolerance."},
            "actions": actions,
            "cost_efficiency": max(0, min(100, efficiency)),
            "authority_boundary": "advisory_only",
        }
