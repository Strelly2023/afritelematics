from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SyncEnvelope:
    semantic_hash: str
    proof_hash: str
    payload: dict[str, Any]


def build_sync_envelope(admission_result: dict[str, Any]) -> SyncEnvelope:
    proof = admission_result.get("proof", {})
    return SyncEnvelope(
        semantic_hash=proof.get("normalized_expression_hash", ""),
        proof_hash=proof.get("proof_hash", ""),
        payload=admission_result,
    )
