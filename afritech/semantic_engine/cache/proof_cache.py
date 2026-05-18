from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProofCache:
    _items: dict[str, dict[str, Any]] = field(default_factory=dict)

    def get(self, expression_hash: str) -> dict[str, Any] | None:
        return self._items.get(expression_hash)

    def put(self, expression_hash: str, proof: dict[str, Any]) -> dict[str, Any]:
        self._items[expression_hash] = dict(proof)
        return self._items[expression_hash]

    def has(self, expression_hash: str) -> bool:
        return expression_hash in self._items

    def clear(self) -> None:
        self._items.clear()
