from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class Vote:
    node_id: str
    result_hash: str
    accepted: bool
    proof: Dict[str, Any]
    reason: str = ""


def vote_from_proof(proof: Dict[str, Any], accepted: bool, reason: str = "") -> Vote:
    node_id = proof.get("node")
    result_hash = proof.get("hash")

    if not isinstance(node_id, str):
        node_id = "unknown"

    if not isinstance(result_hash, str):
        result_hash = ""

    return Vote(
        node_id=node_id,
        result_hash=result_hash,
        accepted=accepted,
        proof=proof,
        reason=reason,
    )
