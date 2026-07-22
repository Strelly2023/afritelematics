from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import build_auth_router, build_novacodepro_session_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform, NovaCodeProRepository


def test_ai_design_draft_records_execution_and_requires_human_review(tmp_path: Path) -> None:
    platform = NovaCodeProPlatform(NovaCodeProRepository(tmp_path / "novacodepro.sqlite3"))
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_novacodepro_session_router())
    app.include_router(build_novacodepro_platform_router(platform))
    client = TestClient(app)
    assert client.post("/v1/novacodepro/session/login", json={"email": "platformadministrator.test@afritechnology.com", "password": "NovaCodePro123!", "role": "ADMIN"}).status_code == 200

    draft = client.post("/v1/novacodepro/design/ai/drafts", json={"resource_type": "wireframe", "name": "Generated dashboard", "execution_id": "execution-123", "model": "platform-routed", "provider": "NovaAI", "regions": [{"id": "hero", "type": "Card"}]})
    assert draft.status_code == 200
    body = draft.json()
    assert body["creation_method"] == "AI_GENERATED"
    assert body["created_from_execution_id"] == "execution-123"
    assert body["human_verified"] is False
    assert body["approval_status"] == "DRAFT"

    generations = client.get("/v1/novacodepro/design/ai/generations")
    assert generations.status_code == 200
    assert generations.json()["generations"][0]["human_review_status"] == "PENDING"
