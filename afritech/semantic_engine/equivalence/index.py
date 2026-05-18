from dataclasses import dataclass, field

from afritech.semantic_engine.ir.hasher import hash_expression
from afritech.semantic_engine.optimizer.normalizer import normalize


@dataclass
class EquivalenceIndex:
    _classes: dict[str, set[str]] = field(default_factory=dict)

    def add(self, expression_id: str, expr) -> str:
        normalized_hash = hash_expression(normalize(expr))
        self._classes.setdefault(normalized_hash, set()).add(expression_id)
        return normalized_hash

    def equivalent_ids(self, expr) -> list[str]:
        normalized_hash = hash_expression(normalize(expr))
        return sorted(self._classes.get(normalized_hash, set()))

    def are_equivalent(self, left, right) -> bool:
        return hash_expression(normalize(left)) == hash_expression(normalize(right))
