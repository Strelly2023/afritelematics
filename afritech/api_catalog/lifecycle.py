"""API lifecycle states and compatibility rules."""

from __future__ import annotations

from enum import StrEnum


class ApiLifecycle(StrEnum):
    EXPERIMENTAL = "experimental"
    PREVIEW = "preview"
    PILOT = "pilot"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


LIFECYCLE_RULES: dict[str, str] = {
    ApiLifecycle.EXPERIMENTAL: "no compatibility guarantee",
    ApiLifecycle.PREVIEW: "additive changes allowed",
    ApiLifecycle.PILOT: "controlled external use",
    ApiLifecycle.STABLE: "backward compatibility required",
    ApiLifecycle.DEPRECATED: "supported until published date",
    ApiLifecycle.RETIRED: "unavailable",
}


def requires_backward_compatibility(status: str) -> bool:
    return status in {ApiLifecycle.STABLE, ApiLifecycle.DEPRECATED}
