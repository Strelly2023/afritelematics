"""Dependency resolution for evidence-derived features."""

from __future__ import annotations

from collections.abc import Iterable

from afritech.features import FeatureEvidence


def resolve_feature_order(features: Iterable[FeatureEvidence]) -> tuple[FeatureEvidence, ...]:
    by_id = {feature.id: feature for feature in features}
    resolved: list[FeatureEvidence] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(feature: FeatureEvidence) -> None:
        if feature.id in visited:
            return
        if feature.id in visiting:
            raise ValueError(f"cyclic feature dependency: {feature.id}")
        visiting.add(feature.id)
        for dependency in feature.dependencies:
            if dependency not in by_id:
                raise KeyError(f"missing feature dependency: {feature.id} -> {dependency}")
            visit(by_id[dependency])
        visiting.remove(feature.id)
        visited.add(feature.id)
        resolved.append(feature)

    for feature in features:
        visit(feature)

    return tuple(resolved)


def dependencies_satisfied(feature: FeatureEvidence, completed_ids: set[str]) -> bool:
    return set(feature.dependencies).issubset(completed_ids)


__all__ = ["dependencies_satisfied", "resolve_feature_order"]
