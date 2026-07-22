from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
from afritech.api.auth.jwt_device_auth import build_auth_router,build_novacodepro_session_router
from afritech.api.novacodepro_platform_api import build_novacodepro_platform_router
from afritech.novacodepro import NovaCodeProPlatform,NovaCodeProRepository
def test_approval_rejects_artifact_changed_after_review(tmp_path:Path)->None:
 platform=NovaCodeProPlatform(NovaCodeProRepository(tmp_path/"ncp.sqlite3"));app=FastAPI();app.include_router(build_auth_router());app.include_router(build_novacodepro_session_router());app.include_router(build_novacodepro_platform_router(platform));client=TestClient(app);assert client.post("/v1/novacodepro/session/login",json={"email":"platformadministrator.test@afritechnology.com","password":"NovaCodePro123!","role":"ADMIN"}).status_code==200
 artifact=client.post("/v1/novacodepro/design/wireframes",json={"name":"Reviewed wireframe","regions":[]}).json();approval=client.post("/v1/novacodepro/design/approvals",json={"resource_type":"wireframe","resource_id":artifact["id"],"reviewed_version":artifact["version"],"required_role":"DESIGN"}).json();client.patch(f"/v1/novacodepro/design/wireframes/{artifact['id']}",json={"description":"Changed after review"});response=client.post(f"/v1/novacodepro/design/approvals/{approval['id']}/approve",json={"resource_type":"wireframe","resource_id":artifact["id"]});assert response.status_code==409;assert response.json()["detail"]["code"]=="design_version_conflict"
