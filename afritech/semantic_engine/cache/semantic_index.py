from dataclasses import dataclass, field

from afritech.semantic_engine.ir.schema import Expression, SystemInvalid


@dataclass
class SemanticIndex:
    symbols: dict[str, set[str]] = field(default_factory=dict)
    operators: dict[str, set[str]] = field(default_factory=dict)

    def add(self, program_id: str, expr) -> None:
        for symbol in collect_symbols(expr):
            self.symbols.setdefault(symbol, set()).add(program_id)
        for operator in collect_operators(expr):
            self.operators.setdefault(operator, set()).add(program_id)

    def programs_for_symbol(self, symbol: str) -> list[str]:
        return sorted(self.symbols.get(symbol, set()))

    def programs_for_operator(self, operator: str) -> list[str]:
        return sorted(self.operators.get(operator, set()))


def collect_symbols(expr) -> set[str]:
    if isinstance(expr, str):
        return {expr}
    if isinstance(expr, tuple):
        return set().union(*(collect_symbols(item) for item in expr)) if expr else set()
    if isinstance(expr, Expression):
        return set().union(*(collect_symbols(item) for item in expr.operands)) if expr.operands else set()
    raise SystemInvalid("invalid_ir_node")


def collect_operators(expr) -> set[str]:
    if isinstance(expr, str):
        return set()
    if isinstance(expr, tuple):
        return set().union(*(collect_operators(item) for item in expr)) if expr else set()
    if isinstance(expr, Expression):
        nested = set().union(*(collect_operators(item) for item in expr.operands)) if expr.operands else set()
        return {expr.operator} | nested
    raise SystemInvalid("invalid_ir_node")
