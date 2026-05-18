from dataclasses import dataclass, field
from typing import Any

from afritech.semantic_engine.ir.hasher import hash_expression
from afritech.semantic_engine.optimizer.normalizer import normalize
from afritech.semantic_engine.proof.proof_builder import validate_proof


@dataclass
class ProofCanonicalStore:
    _proofs: dict[str, dict[str, Any]] = field(default_factory=dict)

    def store(self, expr, proof: dict[str, Any]) -> str:
        normalized = normalize(expr)
        validate_proof(proof, normalized)
        expression_hash = hash_expression(normalized)
        self._proofs[expression_hash] = dict(proof)
        return expression_hash

    def load(self, expression_hash: str) -> dict[str, Any] | None:
        return self._proofs.get(expression_hash)

    def list_hashes(self) -> list[str]:
        return sorted(self._proofs)
