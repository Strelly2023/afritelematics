import hashlib
import json

from afritech.semantic_engine.ir.hasher import canonical_json, hash_expression
from afritech.semantic_engine.ir.schema import SystemInvalid


PROOF_PIPELINE = "compile.normalize.hash.evaluate.proof"


def _proof_payload(expression_hash: str, result: bool) -> dict:
    return {
        "pipeline": PROOF_PIPELINE,
        "evaluated": bool(result),
        "normalized": True,
        "normalized_expression_hash": expression_hash,
        "dependency_graph": [],
    }


def _proof_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_proof(expr, result):
    expression_hash = hash_expression(expr)
    payload = _proof_payload(expression_hash, result)
    return {
        **payload,
        "canonical_expression": canonical_json(expr),
        "proof_hash": _proof_hash(payload),
    }


def validate_proof(proof: dict, expr) -> bool:
    if not isinstance(proof, dict):
        raise SystemInvalid("proof_invalid")

    required = {
        "pipeline",
        "evaluated",
        "normalized",
        "normalized_expression_hash",
        "dependency_graph",
        "proof_hash",
        "canonical_expression",
    }
    missing = required - proof.keys()
    if missing:
        raise SystemInvalid(f"proof_missing_fields:{sorted(missing)}")

    expression_hash = hash_expression(expr)
    if proof["normalized_expression_hash"] != expression_hash:
        raise SystemInvalid("hash_mismatch")
    if proof["canonical_expression"] != canonical_json(expr):
        raise SystemInvalid("proof_expression_mismatch")
    if proof["pipeline"] != PROOF_PIPELINE or proof["normalized"] is not True:
        raise SystemInvalid("proof_invalid")
    if not isinstance(proof["dependency_graph"], list):
        raise SystemInvalid("proof_invalid")

    payload = _proof_payload(expression_hash, bool(proof["evaluated"]))
    if proof["proof_hash"] != _proof_hash(payload):
        raise SystemInvalid("proof_invalid")

    return True
