from afritech.semantic_engine.evaluator.evaluator import evaluate
from afritech.semantic_engine.optimizer.normalizer import normalize
from afritech.semantic_engine.proof.proof_builder import build_proof


def admissible(expr, truth_values: dict[str, bool], declared_symbols: frozenset[str]):

    normalized = normalize(expr)

    result = evaluate(normalized, truth_values, declared_symbols)

    proof = build_proof(normalized, result)

    return result, proof, normalized
