from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novacodepro_product_factory_api import build_novacodepro_product_factory_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository, ProductFactoryService


def _client(tmp_path: Path) -> TestClient:
    repository = NovaCodeProRepository(tmp_path / "novacodepro.sqlite3")
    platform = NovaCodeProPlatform(repository)
    service = ProductFactoryService(platform)
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_product_factory_router(service))
    return TestClient(app)


def _headers(tenant: str = "novatech", user_id: str = "product-admin") -> dict[str, str]:
    token = JWT.create_token(
        user_id,
        role="ADMIN",
        organization_id=tenant,
        tenant_id=tenant,
        permissions=("workspace.read",),
    )
    return {"Authorization": f"Bearer {token}"}


def test_product_factory_api_supports_governed_lifecycle(tmp_path: Path) -> None:
    client = _client(tmp_path)
    headers = _headers()

    guard = client.get("/v1/product-factory")
    assert guard.status_code == 401

    overview = client.get("/v1/product-factory", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["summary"]["requests"] == 0

    request = client.post(
        "/v1/product-factory/requests",
        headers={**headers, "Idempotency-Key": "request-1"},
        json={
            "product_name": "NovaFactory One",
            "product_description": "Digital product factory request",
            "core_business_problem": "Create governed product delivery",
            "target_market": "Enterprise",
            "product_category": "Digital Product Factory",
            "geographic_scope": "Australia",
            "supported_languages": ["en-AU"],
            "supported_currencies": ["AUD"],
            "status": "Draft",
        },
    )
    assert request.status_code == 200
    request_id = request.json()["id"]

    blueprint = client.post(
        f"/v1/product-factory/requests/{request_id}/blueprints",
        headers=headers,
        json={
            "vision": "Deliver products safely and quickly.",
            "mission": "Take products from idea to production with traceability.",
            "recommended_architecture": "NovaCodePro platform",
            "technology_profile": "React and FastAPI",
            "delivery_strategy": "Iterative governance",
            "status": "Draft",
        },
    )
    assert blueprint.status_code == 200
    blueprint_id = blueprint.json()["id"]

    approved_blueprint = client.post(f"/v1/product-factory/blueprints/{blueprint_id}/approve", headers=headers, json={"evidence": [blueprint_id]})
    assert approved_blueprint.status_code == 200
    assert approved_blueprint.json()["status"] == "Approved"

    phases = client.get("/v1/product-factory/phases", headers=headers)
    assert phases.status_code == 200
    phase_id = phases.json()["phases"][0]["id"]
    transitioned = client.post(f"/v1/product-factory/phases/{phase_id}/transition", headers=headers, json={"status": "Ready", "note": "Prepared"})
    assert transitioned.status_code == 200

    evidence = client.post(
        "/v1/product-factory/evidence",
        headers=headers,
        json={"title": "Blueprint evidence", "type": "artifact", "subject": blueprint_id, "blueprint_id": blueprint_id, "result": "PASS"},
    )
    assert evidence.status_code == 200
    assert evidence.json()["verification_status"] == "PASS"

    gate = client.post(
        "/v1/product-factory/gates",
        headers=headers,
        json={"name": "Blueprint gate", "phase_id": phase_id, "decision": "Approved", "decision_maker": "product-admin", "role": "ADMIN", "linked_commit": "commit-1"},
    )
    assert gate.status_code == 200

    improvement = client.post(
        "/v1/product-factory/improvements",
        headers=headers,
        json={"title": "Add traceability export", "description": "Expose export controls", "priority": "high"},
    )
    assert improvement.status_code == 200

    requirement = client.post(
        "/v1/product-factory/requirements",
        headers=headers,
        json={
            "product_id": "product-factory",
            "blueprint_id": blueprint_id,
            "title": "Traceability requirement",
            "statement": "Maintain governed traceability",
            "class": "Functional",
            "mandatory_for_ga": True,
        },
    )
    assert requirement.status_code == 200
    requirement_id = requirement.json()["id"]

    trace_link = client.post(
        "/v1/product-factory/traceability/links",
        headers=headers,
        json={
            "source_entity_type": "requirement",
            "source_entity_id": requirement_id,
            "target_entity_type": "blueprint",
            "target_entity_id": blueprint_id,
            "relationship_type": "supports",
            "status": "DRAFT",
        },
    )
    assert trace_link.status_code == 200

    lifecycle_template = client.post("/v1/product-factory/lifecycle-templates", headers=headers, json={"name": "Factory lifecycle"})
    assert lifecycle_template.status_code == 200
    lifecycle = client.post(f"/v1/product-factory/products/{request_id}/lifecycles", headers=headers, json={"template_id": lifecycle_template.json()["id"]})
    assert lifecycle.status_code == 200
    lifecycle_id = lifecycle.json()["id"]
    assert client.post(f"/v1/product-factory/lifecycles/{lifecycle_id}/start", headers=headers).status_code == 200
    assert client.get(f"/v1/product-factory/lifecycles/{lifecycle_id}/readiness", headers=headers).status_code == 200

    workflow_definition = client.post("/v1/product-factory/workflows/definitions", headers=headers, json={"name": "Release workflow", "steps": ["review", "approve"]})
    assert workflow_definition.status_code == 200
    workflow_instance = client.post("/v1/product-factory/workflows/instances", headers=headers, json={"definition_id": workflow_definition.json()["id"], "product_id": "product-factory"})
    assert workflow_instance.status_code == 200
    assert client.post(f"/v1/product-factory/workflows/instances/{workflow_instance.json()['id']}/approve", headers=headers).status_code == 200

    release = client.post("/v1/product-factory/releases", headers=headers, json={"product_id": "product-factory", "name": "Factory release"})
    assert release.status_code == 200
    release_id = release.json()["id"]
    assert client.post(f"/v1/product-factory/releases/{release_id}/candidates", headers=headers, json={"candidate_id": blueprint_id, "commit_sha": "commit-1"}).status_code == 200
    assert client.post(f"/v1/product-factory/releases/{release_id}/evaluate", headers=headers).status_code == 200
    assert client.get(f"/v1/product-factory/releases/{release_id}/readiness", headers=headers).status_code == 200
    assert client.get(f"/v1/product-factory/reports/catalog", headers=headers).status_code == 200
    assert client.post("/v1/product-factory/search", headers=headers, json={"query": "factory"}).status_code == 200
    assert client.get("/v1/product-factory/cross-product/graph", headers=headers).status_code == 200
    assert client.post("/v1/product-factory/migrations", headers=headers, json={"product_id": "product-factory", "source_system": "legacy", "target_system": "factory"}).status_code == 200
    assert client.get(f"/v1/product-factory/prr/{release_id}", headers=headers).status_code == 200

    demo = client.post("/v1/product-factory/demo", headers=headers)
    assert demo.status_code == 200
    assert demo.json()["name"] in {"NovaFactory Demo", "NovaFactory One"}

    cross_tenant = client.get(f"/v1/product-factory/requests/{request_id}", headers=_headers("other-tenant", "other-admin"))
    assert cross_tenant.status_code == 404


def test_product_factory_api_rejects_invalid_status(tmp_path: Path) -> None:
    client = _client(tmp_path)
    headers = _headers()

    response = client.post(
        "/v1/product-factory/requests",
        headers=headers,
        json={"product_name": "Bad Request", "status": "NotAState"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_status"
