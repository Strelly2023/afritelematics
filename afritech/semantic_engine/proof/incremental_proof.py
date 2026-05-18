from afritech.semantic_engine.cache.proof_canonical_store import ProofCanonicalStore
from afritech.semantic_engine.ir.hasher import hash_expression
from afritech.semantic_engine.optimizer.normalizer import normalize
from afritech.semantic_engine.proof.proof_builder import build_proof


class IncrementalProofBuilder:
    def __init__(self, store: ProofCanonicalStore | None = None):
        self.store = store or ProofCanonicalStore()

    def build_or_reuse(self, expr, result: bool) -> tuple[dict, bool]:
        normalized = normalize(expr)
        expression_hash = hash_expression(normalized)
        cached = self.store.load(expression_hash)
        if cached is not None and cached.get("evaluated") is bool(result):
            return cached, True

        proof = build_proof(normalized, result)
        self.store.store(normalized, proof)
        return proof, False
