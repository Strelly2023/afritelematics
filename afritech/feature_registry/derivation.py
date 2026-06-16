"""Evidence-derived feature projection engine."""

from __future__ import annotations

from afritech.feature_registry.dependency_graph import (
    dependencies_satisfied,
    resolve_feature_order,
)
from afritech.features import EvidenceArtifact, FeatureEvidence, evidence_complete


def derive_features(
    candidates: tuple[FeatureEvidence, ...],
    evidence_index: dict[str, EvidenceArtifact],
) -> tuple[FeatureEvidence, ...]:
    derived: list[FeatureEvidence] = []
    completed_ids: set[str] = set()

    for candidate in resolve_feature_order(candidates):
        if not dependencies_satisfied(candidate, completed_ids):
            continue
        if not evidence_complete(candidate, evidence_index):
            continue
        derived.append(candidate)
        completed_ids.add(candidate.id)

    return tuple(derived)


__all__ = ["derive_features"]
