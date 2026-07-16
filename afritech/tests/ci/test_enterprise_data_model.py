from __future__ import annotations

import pytest

from afritech.data_governance.enterprise import (
    EnterpriseDataGateway,
    EnterpriseDataGovernanceError,
    default_enterprise_data_model,
    enterprise_data_manifest,
    validate_enterprise_data_model,
)


def test_default_enterprise_data_model_includes_shared_core_and_product_domains() -> None:
    model = default_enterprise_data_model()

    assert validate_enterprise_data_model(model) is True
    assert model.shared_entity("Person").source_of_truth == "novaid"
    assert model.shared_entity("Consent").source_of_truth == "novaconsent"
    assert model.product_domain("novaride").schema_name == "novaride"
    assert model.product_domain("novapay").schema_name == "novapay"
    assert model.product_extension("novaride", "Person").table_name == "novaride.driver_profile"

    manifest = enterprise_data_manifest(model)
    assert manifest["validation"]["status"] == "PASS"
    assert manifest["summary"]["shared_entity_count"] >= 10
    assert manifest["summary"]["product_domain_count"] >= 8


def test_enterprise_data_gateway_projects_payload_to_allowed_fields() -> None:
    gateway = EnterpriseDataGateway(default_enterprise_data_model())

    payload = {
        "person_id": "person-1",
        "verification_status": "VERIFIED",
        "legal_name": "Test Rider",
        "date_of_birth_verified": True,
        "country": "AU",
        "wallet_limit": "should_not_leak",
    }

    projected = gateway.project_contract_payload("identity_verified_to_novaride", payload)
    assert projected == {
        "person_id": "person-1",
        "verification_status": "VERIFIED",
        "legal_name": "Test Rider",
        "date_of_birth_verified": True,
        "country": "AU",
    }

    with pytest.raises(EnterpriseDataGovernanceError, match="purpose mismatch"):
        gateway.authorize_projection(
            "identity_verified_to_novaride",
            consumer_product="novaride",
            purpose="wallet_risk",
        )


def test_domain_event_envelope_hash_and_manifest_are_stable() -> None:
    from afritech.data_governance.enterprise import DomainEventEnvelope

    envelope = DomainEventEnvelope(
        event_id="event-1",
        event_type="identity.verified.v1",
        event_version=1,
        producer_product="novaid",
        tenant_id="tenant-1",
        organization_id="org-1",
        subject_id="person-1",
        occurred_at="2026-07-16T00:00:00Z",
        correlation_id="corr-1",
        classification="RESTRICTED",
        payload={"person_id": "person-1", "verification_status": "VERIFIED"},
    )

    assert envelope.evidence_hash.startswith("sha256:")
    assert envelope.canonical_dict()["event_type"] == "identity.verified.v1"
    assert envelope.canonical_dict()["payload"]["person_id"] == "person-1"
