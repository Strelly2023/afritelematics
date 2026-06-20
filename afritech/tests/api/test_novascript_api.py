from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.novascript_api import build_novascript_router


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novascript_router())
    return TestClient(app)


def auth_headers(
    role: str = "DEVELOPER",
    user_id: str = "dev-1",
    organization_id: str = "org-nova",
) -> dict[str, str]:
    token = JWT.create_token(user_id, role=role, organization_id=organization_id)
    return {"Authorization": f"Bearer {token}"}


def test_novascript_catalog_and_status_explain_product_boundary() -> None:
    client = build_client()

    status = client.get("/v1/novascript/status", headers=auth_headers(role="OBSERVER"))
    assert status.status_code == 200
    assert status.json()["product"] == "NovaScript"
    assert status.json()["governed_by"] == "NovaProgramming"
    assert "model_layer" in status.json()

    model_status = client.get("/v1/novascript/model/status", headers=auth_headers(role="OPERATOR"))
    assert model_status.status_code == 200
    assert model_status.json()["model_layer"]["available"] is True

    catalog = client.get("/v1/novascript/catalog", headers=auth_headers(role="OPERATOR"))
    assert catalog.status_code == 200
    body = catalog.json()
    assert body["capabilities"][0] == "code_generation"
    assert body["relationship"]["builds"] == "NovaProgramming"
    assert "prompt_registry" in body["model_layer"]

    prompts = client.get("/v1/novascript/prompts", headers=auth_headers(role="DEVELOPER"))
    assert prompts.status_code == 200
    assert any(template["name"] == "generate" for template in prompts.json())


def test_novascript_generation_and_explanation_are_development_time_only() -> None:
    client = build_client()

    generated = client.post(
        "/v1/novascript/generate",
        json={
            "prompt": "Build a FastAPI endpoint with tests",
            "project_id": "project-employee-rbac",
            "language": "python",
            "mode": "code",
        },
        headers=auth_headers(role="DEVELOPER", user_id="dev-2"),
    )
    assert generated.status_code == 200
    generated_body = generated.json()
    assert generated_body["view"] == "novascript_generation"
    assert generated_body["generated_files"]
    assert generated_body["execution_preview"]["sandboxed"] is True
    assert generated_body["model_layer"]["model_name"]
    assert generated_body["governance_receipt"]["trust_score"] >= 0

    explanation = client.post(
        "/v1/novascript/explain",
        json={"code": "from fastapi import FastAPI\napp = FastAPI()", "context": "demo"},
        headers=auth_headers(role="VERIFIER", user_id="verifier-1"),
    )
    assert explanation.status_code == 200
    assert explanation.json()["summary"]["purpose"] == "API surface or route handler"


def test_novascript_debug_architecture_docs_and_repo_intelligence() -> None:
    client = build_client()

    debug = client.post(
        "/v1/novascript/debug",
        json={"error": "ImportError: module not found", "context": "bootstrap"},
        headers=auth_headers(role="OBSERVER", user_id="observer-1"),
    )
    assert debug.status_code == 200
    assert "missing dependency" in debug.json()["findings"][0]

    architecture = client.post(
        "/v1/novascript/architecture",
        json={"description": "Design a secure API with auth and events", "stack": "FastAPI + PostgreSQL"},
        headers=auth_headers(role="DEVELOPER", user_id="dev-3"),
    )
    assert architecture.status_code == 200
    assert "identity" in architecture.json()["recommended_components"]

    docs = client.post(
        "/v1/novascript/docs",
        json={"topic": "NovaScript product brief", "audience": "developer", "format": "README"},
        headers=auth_headers(role="DEVELOPER", user_id="dev-3"),
    )
    assert docs.status_code == 200
    assert docs.json()["outline"][0] == "Overview of NovaScript product brief"

    repo = client.get(
        "/v1/novascript/repo/project-employee-rbac/intelligence?focus=repo intelligence",
        headers=auth_headers(role="VERIFIER", user_id="verifier-2"),
    )
    assert repo.status_code == 200
    assert repo.json()["product"] == "NovaScript"
    assert repo.json()["relationship"]["builds"] == "NovaProgramming"

    memory = client.get(
        "/v1/novascript/memory/project-employee-rbac",
        headers=auth_headers(role="OPERATOR"),
    )
    assert memory.status_code == 200
    assert memory.json()["project_id"] == "project-employee-rbac"

    receipts = client.get(
        "/v1/novascript/receipts/project-employee-rbac",
        headers=auth_headers(role="OPERATOR"),
    )
    assert receipts.status_code == 200
    assert isinstance(receipts.json(), list)
