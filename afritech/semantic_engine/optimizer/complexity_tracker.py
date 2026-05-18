from dataclasses import dataclass, field

from afritech.semantic_engine.ir.schema import Expression, SystemInvalid


@dataclass(frozen=True)
class ComplexityMetrics:
    nodes: int
    depth: int
    symbols: int
    operators: dict[str, int] = field(default_factory=dict)


def track_complexity(expr) -> ComplexityMetrics:
    operators: dict[str, int] = {}
    symbols: set[str] = set()

    def walk(node, depth: int) -> tuple[int, int]:
        if isinstance(node, str):
            symbols.add(node)
            return 1, depth
        if isinstance(node, tuple):
            if not node:
                return 1, depth
            child = [walk(item, depth + 1) for item in node]
            return 1 + sum(count for count, _ in child), max(d for _, d in child)
        if isinstance(node, Expression):
            operators[node.operator] = operators.get(node.operator, 0) + 1
            if not node.operands:
                return 1, depth
            child = [walk(item, depth + 1) for item in node.operands]
            return 1 + sum(count for count, _ in child), max(d for _, d in child)
        raise SystemInvalid("invalid_ir_node")

    nodes, depth = walk(expr, 1)
    return ComplexityMetrics(
        nodes=nodes,
        depth=depth,
        symbols=len(symbols),
        operators=dict(sorted(operators.items())),
    )
