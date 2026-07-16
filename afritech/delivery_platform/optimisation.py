"""Optimisation planning for delivery targets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import ArtifactRecord, OptimisationPolicy


@dataclass(frozen=True, slots=True)
class OptimisationRecommendation:
    action: str
    target: str
    reason: str
    approval_required: bool


@dataclass(frozen=True, slots=True)
class OptimisationPlan:
    product_code: str
    component: str
    recommendations: tuple[OptimisationRecommendation, ...]
    analysis: dict[str, Any]


@dataclass
class OptimisationEngine:
    def analyse(self, artifact: ArtifactRecord, policy: OptimisationPolicy | None = None) -> OptimisationPlan:
        def _value(item: Any, key: str, fallback: Any = "") -> Any:
            if item is None:
                return fallback
            if isinstance(item, dict):
                return item.get(key, fallback)
            return getattr(item, key, fallback)

        recommendations: list[OptimisationRecommendation] = []
        if artifact.bundle_size_bytes and artifact.bundle_size_bytes > 512_000:
            recommendations.append(
                OptimisationRecommendation(
                    action="code_split",
                    target=artifact.component_name,
                    reason="Bundle exceeds the preferred shell budget.",
                    approval_required=False,
                )
            )
        cache_profile = _value(policy, "cache_profile", "standard-read")
        if policy and cache_profile and cache_profile != "no-cache":
            recommendations.append(
                OptimisationRecommendation(
                    action="cache_tune",
                    target=artifact.component_name,
                    reason=f"Apply cache profile {cache_profile}.",
                    approval_required=False,
                )
            )
        cost_budget = _value(policy, "cost_budget", {})
        if policy and cost_budget and cost_budget.get("monthly", 0) > 0:
            recommendations.append(
                OptimisationRecommendation(
                    action="cost_review",
                    target=artifact.component_name,
                    reason="Cost budget should be reviewed against deployment profile.",
                    approval_required=True,
                )
            )
        return OptimisationPlan(
            product_code=artifact.product_code,
            component=artifact.component_name,
            recommendations=tuple(recommendations),
            analysis={
                "artifact_id": artifact.artifact_id,
                "artifact_checksum": artifact.artifact_checksum,
                "bundle_size_bytes": artifact.bundle_size_bytes,
                "promotion_status": artifact.promotion_status,
            },
        )
