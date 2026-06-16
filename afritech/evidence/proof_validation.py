"""Proof admissibility checks for feature-registry evidence."""

from __future__ import annotations

from afritech.features import (
    EvidenceArtifact,
    EvidenceRef,
    FeatureEvidence,
    authority_chain_valid,
    proof_admissible as _proof_admissible,
    proof_hash_matches_replay,
    valid_proof_payload,
)


def proof_signature_valid(payload: dict[str, object]) -> bool:
    signature = payload.get("signature")
    if signature is None:
        return True
    return isinstance(signature, str) and len(signature) > 0


def proof_admissible(
    evidence_ref: EvidenceRef,
    feature: FeatureEvidence,
    evidence_index: dict[str, EvidenceArtifact] | None = None,
) -> bool:
    return (
        valid_proof_payload(evidence_ref)
        and proof_hash_matches_replay(evidence_ref, feature, evidence_index)
        and _proof_admissible(evidence_ref, feature, evidence_index)
    )


__all__ = [
    "authority_chain_valid",
    "proof_admissible",
    "proof_hash_matches_replay",
    "proof_signature_valid",
    "valid_proof_payload",
]
