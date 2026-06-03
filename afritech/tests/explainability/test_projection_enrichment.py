from afritech.explainability.projection_enrichment import (
    ENFORCEMENT_AUTHORITY,
    ENRICHMENT_STATUS,
    PROJECTION_DISPLAY_ONLY,
    RECEIPT_MUTATION,
    RUNTIME_AUTHORITY,
    VALIDATION_AUTHORITY,
    enrich_explanation_payload,
    enrich_governance_references,
)


def test_projection_enrichment_flags_are_non_authoritative():
    assert ENRICHMENT_STATUS == "READ_ONLY_PROJECTION_ENRICHMENT"
    assert RUNTIME_AUTHORITY is False
    assert ENFORCEMENT_AUTHORITY is False
    assert VALIDATION_AUTHORITY is False
    assert RECEIPT_MUTATION is False
    assert PROJECTION_DISPLAY_ONLY is True


def test_enrich_governance_references_adds_display_metadata_only():
    references = [
        {"type": "ADR", "id": "ADR-0016"},
        {"type": "RULE", "id": "RULE-016-4"},
    ]

    projection_index = {
        "ADR-0016": {
            "title": "Multi-Source Consensus",
            "description": "Governance doctrine for external trust scoring.",
        },
        "RULE-016-4": {
            "title": "External Trust Boundary",
            "description": "External trust cannot become runtime authority.",
        },
    }

    enriched = enrich_governance_references(references, projection_index)

    assert enriched == [
        {
            "type": "ADR",
            "id": "ADR-0016",
            "title": "Multi-Source Consensus",
            "description": "Governance doctrine for external trust scoring.",
            "source": "governance_projection",
            "display_only": True,
        },
        {
            "type": "RULE",
            "id": "RULE-016-4",
            "title": "External Trust Boundary",
            "description": "External trust cannot become runtime authority.",
            "source": "governance_projection",
            "display_only": True,
        },
    ]


def test_enrich_explanation_payload_does_not_mutate_original():
    payload = {
        "execution_id": "exec-001",
        "governance_traceability": [{"type": "ADR", "id": "ADR-0018"}],
    }

    projection_index = {
        "ADR-0018": {
            "title": "Cross-System Continuity",
            "description": "Federated proof remains non-runtime-authoritative.",
        }
    }

    enriched = enrich_explanation_payload(payload, projection_index)

    assert "projection_enrichment" not in payload
    assert enriched["projection_enrichment"] == [
        {
            "type": "ADR",
            "id": "ADR-0018",
            "title": "Cross-System Continuity",
            "description": "Federated proof remains non-runtime-authoritative.",
            "source": "governance_projection",
            "display_only": True,
        }
    ]

    assert enriched["runtime_authority"] is False
    assert enriched["enforcement_authority"] is False
    assert enriched["validation_authority"] is False