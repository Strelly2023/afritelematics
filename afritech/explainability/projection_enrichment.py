"""Read-only projection enrichment for execution explanations.

This module adds human-readable governance metadata to explanation output.

It is explicitly non-authoritative:
- no runtime authority
- no enforcement authority
- no validation authority
- no receipt mutation
- no governance mutation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

ENRICHMENT_STATUS = "READ_ONLY_PROJECTION_ENRICHMENT"
RUNTIME_AUTHORITY = False
ENFORCEMENT_AUTHORITY = False
VALIDATION_AUTHORITY = False
RECEIPT_MUTATION = False
PROJECTION_DISPLAY_ONLY = True


@dataclass(frozen=True)
class ProjectionSummary:
    """Read-only display summary for a governance reference."""

    ref_type: str
    ref_id: str
    title: str
    description: str
    source: str = "governance_projection"
    display_only: bool = True

    def canonical_dict(self) -> dict[str, object]:
        return {
            "type": self.ref_type,
            "id": self.ref_id,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "display_only": self.display_only,
        }


def enrich_governance_references(
    references: Sequence[Mapping[str, str]],
    projection_index: Mapping[str, Mapping[str, str]],
) -> list[dict[str, object]]:
    """Return display-only enriched governance references.

    `projection_index` is supplied by the caller as already-read display data.
    This function does not import projection models, query a database, load YAML,
    or resolve authority.
    """

    enriched: list[dict[str, object]] = []

    for reference in references:
        ref_type = reference.get("type", "")
        ref_id = reference.get("id", "")

        projection = projection_index.get(ref_id, {})

        summary = ProjectionSummary(
            ref_type=ref_type,
            ref_id=ref_id,
            title=projection.get("title", ""),
            description=projection.get("description", ""),
        )

        enriched.append(summary.canonical_dict())

    return enriched


def enrich_explanation_payload(
    explanation_payload: Mapping[str, object],
    projection_index: Mapping[str, Mapping[str, str]],
) -> dict[str, object]:
    """Return a copied explanation payload with read-only projection enrichment."""

    copied = dict(explanation_payload)

    raw_refs = copied.get("governance_traceability", [])
    references: list[Mapping[str, str]] = []

    if isinstance(raw_refs, list):
        for item in raw_refs:
            if isinstance(item, dict):
                ref_type = item.get("type")
                ref_id = item.get("id")
                if isinstance(ref_type, str) and isinstance(ref_id, str):
                    references.append({"type": ref_type, "id": ref_id})

    copied["projection_enrichment"] = enrich_governance_references(
        references=references,
        projection_index=projection_index,
    )

    copied["projection_enrichment_status"] = ENRICHMENT_STATUS
    copied["projection_display_only"] = PROJECTION_DISPLAY_ONLY
    copied["runtime_authority"] = RUNTIME_AUTHORITY
    copied["enforcement_authority"] = ENFORCEMENT_AUTHORITY
    copied["validation_authority"] = VALIDATION_AUTHORITY

    return copied