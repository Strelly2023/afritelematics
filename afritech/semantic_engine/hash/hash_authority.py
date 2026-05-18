from afritech.semantic_engine.ir.hasher import hash_expression
from afritech.semantic_engine.optimizer.normalizer import normalize


def canonical_semantic_hash(expr) -> str:
    return hash_expression(normalize(expr))
