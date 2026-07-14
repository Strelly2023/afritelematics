from __future__ import annotations

from afritech.api_catalog.provenance import publication_provenance, validate_publication_provenance
from afritech.api_catalog.registry import get_api_catalog


def test_publication_provenance_contains_release_identity() -> None:
    contract = get_api_catalog().get("novapay")
    provenance = publication_provenance(contract)
    assert provenance["domain"] == "novapay"
    assert provenance["release_id"] == "api-novapay-2026.07.0"
    assert provenance["published_at"]


def test_production_unknown_provenance_is_rejected() -> None:
    issues = validate_publication_provenance(
        {"git_commit": "unknown", "build_id": "local", "pipeline_id": "local", "release_id": "api-test"},
        production=True,
    )
    assert {"git_commit", "build_id", "pipeline_id"}.issubset(set(issues))
