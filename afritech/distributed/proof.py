from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


# ---------------------------------------------------------
# Deterministic hashing
# ---------------------------------------------------------

def hash_result(result: Any) -> str:
    """
    Deterministic hash of execution result.

    Ensures:
    - Same data → same hash across all nodes
    - Stable for consensus comparison
    """

    try:
        serialized = json.dumps(
            result,
            sort_keys=True,       # ✅ deterministic ordering
            separators=(",", ":"),  # ✅ remove whitespace differences
            default=str           # ✅ fallback for non-serializable
        )
    except Exception:
        # ✅ fallback (never fail hashing)
        serialized = str(result)

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# ---------------------------------------------------------
# Proof construction
# ---------------------------------------------------------

def build_proof(
    node_id: str,
    result: Any,
    signature: bytes,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Build a cryptographic execution proof.

    Structure:
    {
        "node": str,
        "result": Any,
        "hash": str,
        "signature": hex,
        "metadata": optional
    }
    """

    if not isinstance(node_id, str):
        raise TypeError("node_id must be a string")

    if not isinstance(signature, (bytes, bytearray)):
        raise TypeError("signature must be bytes")

    proof: Dict[str, Any] = {
        "node": node_id,
        "result": result,
        "hash": hash_result(result),
        "signature": signature.hex(),  # ✅ network-friendly format
    }

    # ✅ Optional metadata (epoch, timestamp, etc.)
    if metadata is not None:
        if not isinstance(metadata, dict):
            raise TypeError("metadata must be a dictionary")
        proof["metadata"] = metadata

    return proof


# ---------------------------------------------------------
# Proof validation (local utility, optional but powerful)
# ---------------------------------------------------------

def validate_proof_structure(proof: Dict[str, Any]) -> bool:
    """
    Validate basic proof structure before cryptographic verification.
    """

    required_fields = {"node", "result", "hash", "signature"}

    if not isinstance(proof, dict):
        return False

    if not required_fields.issubset(proof.keys()):
        return False

    if not isinstance(proof["node"], str):
        return False

    if not isinstance(proof["hash"], str):
        return False

    if not isinstance(proof["signature"], str):
        return False

    # ✅ verify hash integrity
    expected_hash = hash_result(proof["result"])

    if expected_hash != proof["hash"]:
        return False

    return True
