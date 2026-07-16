from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.delivery_platform_api import build_delivery_platform_router
from afritech.api.auth.jwt_device_auth import JWTClaims, get_current_claims


def test_delivery_platform_api_supports_validate_build_plan_and_rollback(tmp_path) -> None:
    app = FastAPI()
    app.include_router(build_delivery_platform_router())
    app.dependency_overrides[get_current_claims] = lambda: JWTClaims(
        sub="user-001",
        role="ADMIN",
        organization_id="org-001",
        tenant_id="tenant-001",
        permissions=("platform:delivery:manage",),
    )
    client = TestClient(app)

    manifest = {
        "product_code": "novacodepro",
        "version": "2026.07.0",
        "owner": "NovaCodePro Platform Team",
        "services": [
            {"name": "novacodepro-portal", "image": "registry.afritechnology.com/novacodepro-portal", "port": 80, "replicas": {"minimum": 1, "maximum": 2}}
        ],
        "workers": [],
        "frontends": [{"name": "novacodepro-portal", "build_path": "novacodepro_portal", "hosting_profile": "static-cdn"}],
        "mobile_apps": [],
        "infrastructure": [],
        "migrations": [],
        "scaling_policies": [],
        "optimisation_policies": [],
        "health_checks": [],
        "verification_checks": [],
    }

    validate = client.post("/v1/platform/deployments/products/novacodepro/validate", json=manifest)
    assert validate.status_code == 200

    source = tmp_path / "source"
    source.mkdir()
    (source / "index.html").write_text("<html>NovaCodePro</html>", encoding="utf-8")

    build = client.post(
        "/v1/platform/deployments/products/novacodepro/build",
        json={
            "build_id": "build-001",
            "component_name": "portal",
            "build_profile": "vite",
            "source_path": str(source),
            "output_type": "static",
            "dependency_lockfile": "package-lock.json",
            "build_commands": ["npm run build"],
            "test_commands": ["npm test"],
            "security_commands": ["npm audit"],
            "artifact_name": "novacodepro-portal",
            "artifact_version": "2026.07.0",
            "optimisation_profile": "frontend",
        },
    )
    assert build.status_code == 200
    assert build.json()["artifact"]["promotion_status"] == "VERIFIED"

    plan = client.post(
        "/v1/platform/deployments/products/novacodepro/plan",
        json={"environment": "staging", "region": "AU"},
    )
    assert plan.status_code == 200
    deployment_id = plan.json()["plan"]["deployment_id"]

    deploy = client.post(
        "/v1/platform/deployments/products/novacodepro/deploy",
        json={"deployment_id": deployment_id},
    )
    assert deploy.status_code == 200
    assert deploy.json()["deployment"]["current_state"] == "DEPLOYED"

    verify = client.post("/v1/platform/deployments/products/novacodepro/verify")
    assert verify.status_code == 200
    assert verify.json()["status"] == "PASS"

    optimise = client.post("/v1/platform/optimisation/products/novacodepro/analyse")
    assert optimise.status_code == 200

    rollback = client.post(
        "/v1/platform/deployments/products/novacodepro/rollback",
        json={"deployment_id": deployment_id, "reason": "verification failure"},
    )
    assert rollback.status_code == 200
    assert rollback.json()["deployment"]["current_state"] == "ROLLED_BACK"
