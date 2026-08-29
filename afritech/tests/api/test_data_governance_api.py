from __future__ import annotations

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.data_governance_api import build_data_governance_router
from afritech.data_governance.metadata_repository import (
    DataLineageRecord,
    EnterpriseMetadataRepository,
    EntityMetadata,
    EntityRelationship,
    SchemaMigrationRecord,
)


def build_client(repository: EnterpriseMetadataRepository | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_data_governance_router(repository))
    return TestClient(app)


def auth_headers(role: str = "OPERATOR", user_id: str = "data-operator", organization_id: str = "org-novatech") -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_data_governance_api_exposes_shared_model_and_contracts() -> None:
    client = build_client(EnterpriseMetadataRepository())
    headers = auth_headers()

    overview = client.get("/v1/novatech/data-governance", headers=headers)
    assert overview.status_code == 200
    payload = overview.json()
    assert payload["platform"] == "NovaTech"
    assert payload["model"]["shared_entity_count"] >= 10
    assert any(entity["name"] == "Person" for entity in payload["shared_entities"])
    assert any(domain["product_code"] == "novaride" for domain in payload["product_domains"])
    assert any(contract["contract_id"] == "identity_verified_to_novaride" for contract in payload["contracts"])
    assert any(event["event_type"] == "identity.verified.v1" for event in payload["events"])

    domain = client.get("/v1/novatech/data-governance/domains/novaride", headers=headers)
    assert domain.status_code == 200
    assert domain.json()["domain"]["schema_name"] == "novaride"
    assert domain.json()["extensions"][0]["table_name"] == "novaride.driver_profile"

    contract = client.get(
        "/v1/novatech/data-governance/contracts/identity_verified_to_novaride",
        headers=headers,
    )
    assert contract.status_code == 200
    assert contract.json()["contract"]["consumer_product"] == "novaride"

    event = client.get("/v1/novatech/data-governance/events/identity.verified.v1", headers=headers)
    assert event.status_code == 200
    assert event.json()["event"]["topic"] == "novatech.identity.events"


def test_metadata_api_registers_products_entities_and_lineage(tmp_path) -> None:
    repository = EnterpriseMetadataRepository(path=tmp_path / "enterprise-metadata.yaml")
    client = build_client(repository)
    headers = auth_headers(role="ADMIN")

    product = client.post(
        "/v1/novatech/data-governance/products",
        headers=headers,
        json={
            "product_code": "novafleet",
            "name": "NovaFleet",
            "owner": "Fleet Team",
            "schema_name": "novafleet",
            "version": "2026.07.0",
            "classification": "CONFIDENTIAL",
            "region": "GLOBAL",
            "description": "Fleet operations domain",
            "entities": [
                {
                    "name": "FleetVehicle",
                    "schema_name": "novafleet",
                    "owner": "Fleet Team",
                    "source_of_truth": "novafleet",
                    "classification": "CONFIDENTIAL",
                    "product_code": "novafleet",
                    "fields": ["vehicle_id", "tenant_id", "registration_number"],
                    "business_meaning": "Managed vehicle inventory",
                    "privacy": "internal_only",
                    "example_queries": ["show fleet vehicles"],
                    "tags": ["fleet", "vehicle"],
                }
            ],
            "contracts": [
                {
                    "contract_id": "novaid_to_novafleet",
                    "producer_product": "novaid",
                    "consumer_product": "novafleet",
                    "data_type": "VerifiedIdentity",
                    "schema_version": 1,
                    "purpose": "fleet_onboarding",
                    "allowed_fields": ["person_id", "verification_status"],
                    "retention_policy": "OPERATIONAL",
                    "consent_required": True,
                    "status": "APPROVED",
                    "sharing_level": "ENTERPRISE",
                    "schema_change": "COMPATIBLE",
                    "classification": "RESTRICTED",
                    "topic": "novatech.identity.events",
                }
            ],
            "events": [
                {
                    "event_type": "fleet.vehicle.registered.v1",
                    "event_version": 1,
                    "producer_product": "novafleet",
                    "topic": "novatech.fleet.events",
                    "payload_fields": ["vehicle_id", "tenant_id"],
                    "consumers": ["novaride"],
                    "classification": "CONFIDENTIAL",
                    "sharing_level": "ENTERPRISE",
                    "schema_change": "COMPATIBLE",
                    "retention_policy": "AUDIT",
                }
            ],
            "migrations": [
                {
                    "id": "novafleet_0001",
                    "product_code": "novafleet",
                    "version": "2026.07.0",
                    "checksum": "sha256:abc123",
                    "author": "Fleet Team",
                    "approved_by": "Fleet Architecture",
                    "applied_at": datetime.now(timezone.utc).isoformat(),
                    "rollback_version": "2026.06.0",
                    "status": "APPROVED",
                }
            ],
        },
    )
    assert product.status_code == 200
    assert product.json()["product"]["product_code"] == "novafleet"

    entity = client.get("/v1/platform/entities/FleetVehicle", headers=headers)
    assert entity.status_code == 200
    assert entity.json()["entity"]["business_meaning"] == "Managed vehicle inventory"

    lineage = client.post(
        "/v1/platform/lineage",
        headers=headers,
        json={
            "id": "lineage-1",
            "source_product": "novaid",
            "target_product": "novafleet",
            "data_type": "VerifiedIdentity",
            "purpose": "fleet_onboarding",
            "path": ["novaid", "novafleet", "warehouse"],
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "evidence_hash": "sha256:" + "1" * 64,
            "classification": "RESTRICTED",
            "status": "ACTIVE",
        },
    )
    assert lineage.status_code == 200
    assert lineage.json()["lineage"]["target_product"] == "novafleet"

    graph = client.get("/v1/platform/graph", headers=headers)
    assert graph.status_code == 200
    assert graph.json()["acyclic"] is True
    assert any(node["id"] == "novafleet" for node in graph.json()["nodes"])

    search = client.get("/v1/platform/search", headers=headers, params={"query": "fleet"})
    assert search.status_code == 200
    assert search.json()["search"]["results"]

    reloaded = EnterpriseMetadataRepository.load(repository.path)
    assert reloaded.get_product("novafleet")["schema_name"] == "novafleet"
    assert reloaded.get_entity("FleetVehicle")["business_meaning"] == "Managed vehicle inventory"
    assert reloaded.get_lineage("lineage-1")["path"] == ["novaid", "novafleet", "warehouse"]
