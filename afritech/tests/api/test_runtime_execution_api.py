from __future__ import annotations

import importlib

from fastapi import FastAPI
from fastapi.testclient import TestClient

from afritech.api.auth.jwt_device_auth import JWT, build_auth_router
from afritech.api.executable_runtime_api import build_executable_runtime_router
from afritech.api.runtime_activation_api import build_runtime_activation_router
from afritech.api.runtime_infrastructure_api import build_runtime_infrastructure_router
from afritech.api.runtime_verification_api import build_runtime_verification_router
from afritech.api.runtime_worker_api import build_runtime_worker_router
from afritech.platform_runtime import (
    BackendProductRegistration,
    DeploymentVerifier,
    InfrastructureProvisioner,
    ProductActivationService,
    ProductModuleLoader,
    ProductRegistrationStatus,
    ProductRuntimeRegistry,
    ProductCommandExecutor,
    ProductQueryExecutor,
    RouteRegistry,
    RuntimeEvidenceService,
    WorkerSupervisor,
    ExecutableProductRuntime,
)

from afritech.tests.platform_runtime.conftest import build_fake_module


def _auth_headers(role: str = "ADMIN") -> dict[str, str]:
    token = JWT.create_token("runtime-admin", role=role, organization_id="org-novatech", tenant_id="tenant-a", roles=(role,), permissions=("platform:view",))
    return {"Authorization": f"Bearer {token}"}


def _runtime(tmp_path) -> ExecutableProductRuntime:
    registry = ProductRuntimeRegistry(path=tmp_path / "runtime.yaml")
    registry.register_product(
        BackendProductRegistration(
            product_code="novafleet",
            module_name="afritech.products.novafleet",
            version="2026.07.0",
            owner="Fleet Team",
            api_prefix="/v1/novafleet",
            health_path="/health/products/novafleet",
            database_schema="novafleet",
            status=ProductRegistrationStatus.APPROVED,
            registered_commands=("RegisterFleetVehicle",),
            registered_queries=("GetFleetVehicle",),
            registered_workers=("fleet-worker",),
            registered_consumers=("fleet-consumer",),
            infrastructure={"postgres": "novafleet"},
            configuration={"maintenance_reminder_days": 30},
            module_version="2026.07.0",
        )
    )
    supervisor = WorkerSupervisor()
    return ExecutableProductRuntime(
        registry,
        product_loader=ProductModuleLoader(route_registry=RouteRegistry(), worker_registry=supervisor.worker_registry),
        command_executor=ProductCommandExecutor(RuntimeEvidenceService()),
        query_executor=ProductQueryExecutor(RuntimeEvidenceService()),
        route_registry=RouteRegistry(),
        worker_supervisor=supervisor,
        infrastructure_provisioner=InfrastructureProvisioner(),
        activation_service=ProductActivationService(),
        evidence_service=RuntimeEvidenceService(),
        deployment_verifier=DeploymentVerifier(),
    )


def test_runtime_execution_api_smoke(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(importlib, "import_module", lambda name: build_fake_module())
    runtime = _runtime(tmp_path)
    app = FastAPI()
    app.include_router(build_auth_router())
    app.include_router(build_executable_runtime_router(runtime))
    app.include_router(build_runtime_activation_router(runtime.activation_service))
    app.include_router(build_runtime_worker_router(runtime.worker_supervisor))
    app.include_router(build_runtime_infrastructure_router(runtime.infrastructure_provisioner))
    app.include_router(build_runtime_verification_router(runtime.deployment_verifier))
    client = TestClient(app)
    headers = _auth_headers()

    loaded = client.post("/v1/platform/runtime/products/novafleet/load", headers=headers)
    assert loaded.status_code == 200
    assert loaded.json()["state"] == "LOADED"

    started = client.post("/v1/platform/runtime/products/novafleet/start", headers=headers)
    assert started.status_code == 200
    assert started.json()["state"] == "RUNNING"

    command = client.post(
        "/v1/platform/runtime/products/novafleet/commands/RegisterFleetVehicle",
        headers=headers,
        json={
            "payload": {"payload": {"vehicle_id": "veh-1"}},
            "context": {
                "request_id": "req-1",
                "correlation_id": "corr-1",
                "tenant_id": "tenant-a",
                "organization_id": "org-novatech",
                "actor_id": "runtime-admin",
                "actor_type": "user",
                "environment": "development",
                "region": "AU",
                "language": "en",
                "timezone": "Australia/Melbourne",
                "trace_id": "trace-1",
                "purpose": "testing",
            },
        },
    )
    assert command.status_code == 200
    assert command.json()["result"]["payload"]["vehicle_id"] == "veh-1"

    query = client.post(
        "/v1/platform/runtime/products/novafleet/queries/GetFleetVehicle",
        headers=headers,
        json={
            "payload": {"parameters": {"vehicle_id": "veh-1"}},
            "context": {
                "request_id": "req-1",
                "correlation_id": "corr-1",
                "tenant_id": "tenant-a",
                "organization_id": "org-novatech",
                "actor_id": "runtime-admin",
                "actor_type": "user",
                "environment": "development",
                "region": "AU",
                "language": "en",
                "timezone": "Australia/Melbourne",
                "trace_id": "trace-1",
                "purpose": "testing",
            },
        },
    )
    assert query.status_code == 200
    assert query.json()["result"]["parameters"]["vehicle_id"] == "veh-1"

    validation = client.post(
        "/v1/platform/runtime/activations/novafleet/validate",
        headers=headers,
        json={"version": "2026.07.0", "environment": "public-pilot", "region": "AU"},
    )
    assert validation.status_code == 200
    assert validation.json()["state"] == "REVIEW_REQUIRED"

    approval = client.post(
        "/v1/platform/runtime/activations/novafleet/approve",
        headers=headers,
        json={
            "approval_id": "approval-1",
            "product_code": "novafleet",
            "product_version": "2026.07.0",
            "environment": "public-pilot",
            "decision": "APPROVED",
            "approver_id": "runtime-admin",
            "approver_roles": ["ADMIN"],
            "approved_at": "2026-07-16T00:00:00Z",
            "expires_at": None,
            "conditions": [],
            "evidence_refs": [],
            "checksum": "sha256:" + "1" * 64,
        },
    )
    assert approval.status_code == 200

    assert client.post("/v1/platform/runtime/activations/novafleet/provision", headers=headers, params={"approval_id": "approval-1"}).status_code == 200
    assert client.post("/v1/platform/runtime/activations/novafleet/load", headers=headers, params={"approval_id": "approval-1"}).status_code == 200
    assert client.post("/v1/platform/runtime/activations/novafleet/deploy", headers=headers, params={"approval_id": "approval-1"}).status_code == 200
    assert client.post("/v1/platform/runtime/activations/novafleet/verify", headers=headers, params={"approval_id": "approval-1"}).status_code == 200
    assert client.post("/v1/platform/runtime/activations/novafleet/activate", headers=headers, params={"approval_id": "approval-1"}).status_code == 200

    worker_health = client.get("/v1/platform/runtime/workers/novafleet", headers=headers)
    assert worker_health.status_code == 200
    assert worker_health.json()["product_code"] == "novafleet"

    infrastructure = client.post(
        "/v1/platform/runtime/infrastructure/novafleet/plan",
        headers=headers,
        json={
            "id": "novafleet-postgres",
            "product_code": "novafleet",
            "kind": "postgres_schema",
            "name": "novafleet",
            "required": True,
            "configuration": {"schema": "novafleet"},
            "desired_state": "present",
            "ownership": "product",
            "region": "AU",
        },
    )
    assert infrastructure.status_code == 200
    assert infrastructure.json()["product_code"] == "novafleet"

    verification = client.post(
        "/v1/platform/runtime/verification/novafleet/execute",
        headers=headers,
        json={"version": "2026.07.0", "environment": "public-pilot", "region": "AU"},
    )
    assert verification.status_code == 200
    assert verification.json()["status"] == "PASS"
