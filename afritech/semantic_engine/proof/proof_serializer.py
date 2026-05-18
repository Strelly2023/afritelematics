import json
from typing import Any

from afritech.semantic_engine.ir.schema import SystemInvalid


def proof_to_json(proof: dict[str, Any]) -> str:
    if not isinstance(proof, dict):
        raise SystemInvalid("proof_invalid")
    return json.dumps(proof, sort_keys=True, separators=(",", ":"))


def proof_from_json(payload: str) -> dict[str, Any]:
    try:
        proof = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SystemInvalid(f"invalid_proof_json:{exc.msg}") from exc
    if not isinstance(proof, dict):
        raise SystemInvalid("proof_invalid")
    return proof
