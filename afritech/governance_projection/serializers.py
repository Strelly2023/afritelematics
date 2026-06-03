"""Serializers for read-only governance projection objects."""

from __future__ import annotations

from typing import Any

from .importer import GovernanceProjectionBundle
from .models import DocumentaryProjectionModel


def serialize_projection_model(instance: DocumentaryProjectionModel) -> dict[str, Any]:
    return {
        "type": instance.__class__.__name__,
        "source_path": instance.source_path,
        "source_id": instance.source_id,
        "title": instance.title,
        "projection_status": instance.projection_status,
        "projection_is_documentary_only": instance.projection_is_documentary_only,
        "runtime_authority": instance.runtime_authority,
        "enforcement_authority": instance.enforcement_authority,
        "payload": instance.payload,
    }


def serialize_projection(bundle: GovernanceProjectionBundle) -> dict[str, list[dict[str, Any]]]:
    return {
        "adrs": [serialize_projection_model(item) for item in bundle.adrs],
        "invariants": [serialize_projection_model(item) for item in bundle.invariants],
        "rules": [serialize_projection_model(item) for item in bundle.rules],
        "bindings": [serialize_projection_model(item) for item in bundle.bindings],
        "ci_checks": [serialize_projection_model(item) for item in bundle.ci_checks],
        "non_claims": [serialize_projection_model(item) for item in bundle.non_claims],
        "next_steps": [serialize_projection_model(item) for item in bundle.next_steps],
    }
