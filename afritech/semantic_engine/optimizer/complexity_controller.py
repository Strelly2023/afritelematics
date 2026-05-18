from dataclasses import dataclass

from afritech.semantic_engine.ir.schema import SystemInvalid
from afritech.semantic_engine.optimizer.cost_analyzer import estimate_cost
from afritech.semantic_engine.optimizer.complexity_tracker import track_complexity


@dataclass(frozen=True)
class ComplexityLimits:
    max_nodes: int = 256
    max_depth: int = 32
    max_cost: int = 1024


def enforce_complexity(expr, limits: ComplexityLimits | None = None) -> bool:
    limits = limits or ComplexityLimits()
    metrics = track_complexity(expr)
    cost = estimate_cost(expr)

    if metrics.nodes > limits.max_nodes:
        raise SystemInvalid("complexity_node_limit_exceeded")
    if metrics.depth > limits.max_depth:
        raise SystemInvalid("complexity_depth_limit_exceeded")
    if cost.total > limits.max_cost:
        raise SystemInvalid("complexity_cost_limit_exceeded")

    return True
