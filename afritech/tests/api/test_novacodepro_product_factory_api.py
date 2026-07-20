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
