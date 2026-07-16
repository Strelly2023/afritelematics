from __future__ import annotations

import asyncio
import importlib

import pytest
from dataclasses import replace

from afritech.platform_runtime import (
    BackendProductRegistration,
    ExecutionContext,
    ExecutableProductRuntime,
    ProductActivationService,
    ProductCommandExecutor,
    ProductLoadRejected,
    ProductQueryExecutor,
    ProductRegistrationStatus,
    ProductRuntimeRegistry,
    ProductRuntimeState,
    ProductModuleLoader,
    RouteRegistry,
    RuntimeEvidenceService,
    WorkerSupervisor,
    InfrastructureProvisioner,
    DeploymentVerifier,
)

from .conftest import build_fake_module


def _context() -> ExecutionContext:
    return ExecutionContext(
        request_id="req-1",
        correlation_id="corr-1",
        causation_id=None,
        product_code="novafleet",
        tenant_id="tenant-a",
        organization_id="org-a",
        actor_id="actor-a",
        actor_type="user",
        roles=("ADMIN",),
        permissions=("platform:view",),
        environment="development",
        region="AU",
        language="en",
        timezone="Australia/Melbourne",
        trace_id="trace-1",
        idempotency_key="idem-1",
        purpose="testing",
    )


@pytest.fixture()
def registry(tmp_path) -> ProductRuntimeRegistry:
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
    return registry


def test_executable_runtime_loads_starts_and_snapshots(monkeypatch: pytest.MonkeyPatch, registry: ProductRuntimeRegistry) -> None:
    monkeypatch.setattr(importlib, "import_module", lambda name: build_fake_module())
    runtime = ExecutableProductRuntime(
        registry,
        product_loader=ProductModuleLoader(route_registry=RouteRegistry()),
        command_executor=ProductCommandExecutor(RuntimeEvidenceService()),
        query_executor=ProductQueryExecutor(RuntimeEvidenceService()),
        route_registry=RouteRegistry(),
        worker_supervisor=WorkerSupervisor(),
        infrastructure_provisioner=InfrastructureProvisioner(),
        activation_service=ProductActivationService(),
        evidence_service=RuntimeEvidenceService(),
        deployment_verifier=DeploymentVerifier(),
    )

    loaded = asyncio.run(runtime.load_product("novafleet"))
    assert loaded.product_code == "novafleet"
    assert loaded.state == ProductRuntimeState.LOADED

    start_result = asyncio.run(runtime.start_product("novafleet"))
    assert start_result["state"] == "RUNNING"
    assert runtime.get_loaded_product("novafleet").state == ProductRuntimeState.LOADED

    context = _context()
    loaded_product = replace(runtime.get_loaded_product("novafleet"), state=ProductRuntimeState.RUNNING)
    command = asyncio.run(runtime.command_executor.execute(
        product_code="novafleet",
        command_name="RegisterFleetVehicle",
        payload={"vehicle_id": "veh-1"},
        context=context,
        loaded_product=loaded_product,
    ))
    query = asyncio.run(runtime.query_executor.execute(
        product_code="novafleet",
        query_name="GetFleetVehicle",
        parameters={"vehicle_id": "veh-1"},
        context=context,
        loaded_product=loaded_product,
    ))

    assert command.success is True
    assert command.result["payload"]["vehicle_id"] == "veh-1"
    assert query.success is True
    assert query.result["parameters"]["vehicle_id"] == "veh-1"
    asyncio.run(runtime.quarantine_product("novafleet", "test"))
    snapshot = runtime.snapshot()
    assert snapshot["states"]["novafleet"] == "QUARANTINED"
