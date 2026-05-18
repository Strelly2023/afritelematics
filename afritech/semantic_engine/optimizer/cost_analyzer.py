from dataclasses import dataclass

from afritech.semantic_engine.optimizer.complexity_tracker import (
    ComplexityMetrics,
    track_complexity,
)


@dataclass(frozen=True)
class CostEstimate:
    node_cost: int
    depth_cost: int
    quantifier_cost: int
    total: int


def estimate_cost(expr) -> CostEstimate:
    metrics = track_complexity(expr)
    return estimate_from_metrics(metrics)


def estimate_from_metrics(metrics: ComplexityMetrics) -> CostEstimate:
    node_cost = metrics.nodes
    depth_cost = max(metrics.depth - 1, 0) * 2
    quantifier_cost = metrics.operators.get("FORALL", 0) * max(metrics.symbols, 1)
    return CostEstimate(
        node_cost=node_cost,
        depth_cost=depth_cost,
        quantifier_cost=quantifier_cost,
        total=node_cost + depth_cost + quantifier_cost,
    )
