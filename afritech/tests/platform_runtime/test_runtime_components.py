from __future__ import annotations

import asyncio
import importlib
from dataclasses import replace

import pytest
from fastapi import APIRouter

from afritech.platform_runtime import (
    ActivationState,
    ALLOWED_ACTIVATION_TRANSITIONS,
    BackendProductRegistration,
    DeploymentVerifier,
    ExecutionContext,
    InfrastructureKind,
    InfrastructureProvisioner,
    InfrastructureRequirement,
    ProductActivationBlocked,
    ProductActivationService,
    ProductCommandExecutor,
    ProductExecutionDenied,
    ProductModuleLoader,
    ProductQueryExecutor,
    ProductRegistrationStatus,
    ProductRuntimeRegistry,
    ProductRuntimeState,
    ProductRouteConflict,
    ProtectedConfigurationViolation,
    RouteRegistry,
    RuntimeApproval,
    RuntimeEvidenceService,
    WorkerDefinition,
    WorkerRegistry,
    WorkerSupervisor,
    validate_activation_transition,
    validate_protected_configuration,
)

from .conftest import build_fake_module


def _registration() -> BackendProductRegistration:
    return BackendProductRegistration(
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


def _context(**overrides) -> ExecutionContext:
    payload = dict(
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
    payload.update(overrides)
    return ExecutionContext(**payload)


@pytest.fixture()
def loaded_product(monkeypatch: pytest.MonkeyPatch, tmp_path):
    monkeypatch.setattr(importlib, "import_module", lambda name: build_fake_module())
    registry = ProductRuntimeRegistry(path=tmp_path / "runtime.yaml")
    registry.register_product(_registration())
    loader = ProductModuleLoader(route_registry=RouteRegistry())
    return loader.load(registry._require_product("novafleet"))


def _running_product(loaded_product):
    return replace(loaded_product, state=ProductRuntimeState.RUNNING)


def test_command_executor_honors_tenant_and_idempotency(loaded_product) -> None:
    executor = ProductCommandExecutor(RuntimeEvidenceService())
    context = _context()

    first = asyncio.run(executor.execute(
        product_code="novafleet",
        command_name="RegisterFleetVehicle",
        payload={"vehicle_id": "veh-1"},
        context=context,
        loaded_product=_running_product(loaded_product),
    ))
    second = asyncio.run(executor.execute(
        product_code="novafleet",
        command_name="RegisterFleetVehicle",
        payload={"vehicle_id": "veh-1"},
        context=context,
        loaded_product=_running_product(loaded_product),
    ))

    assert first.success is True
    assert first.result["payload"]["vehicle_id"] == "veh-1"
    assert first.evidence_id == second.evidence_id
    assert first is second


def test_command_executor_rejects_missing_tenant(loaded_product) -> None:
    executor = ProductCommandExecutor(RuntimeEvidenceService())
    with pytest.raises(ProductExecutionDenied, match="tenant_context_required"):
        asyncio.run(executor.execute(
            product_code="novafleet",
            command_name="RegisterFleetVehicle",
            payload={"vehicle_id": "veh-1"},
            context=_context(tenant_id=""),
            loaded_product=_running_product(loaded_product),
        ))


def test_query_executor_applies_context(loaded_product) -> None:
    executor = ProductQueryExecutor(RuntimeEvidenceService())
    result = asyncio.run(executor.execute(
        product_code="novafleet",
        query_name="GetFleetVehicle",
        parameters={"vehicle_id": "veh-1"},
        context=_context(),
        loaded_product=_running_product(loaded_product),
    ))

    assert result.success is True
    assert result.result["parameters"]["vehicle_id"] == "veh-1"


def test_route_registry_accepts_product_routes_and_rejects_platform_routes() -> None:
    registry = RouteRegistry()
    router = APIRouter(prefix="/v1/novafleet")

    @router.get("/ping")
    def ping() -> dict[str, str]:
        return {"status": "ok"}

    registrations = registry.validate_product_routes("novafleet", (router,))
    assert registrations[0].path == "/v1/novafleet/ping"

    protected = APIRouter()

    @protected.get("/v1/platform/runtime")
    def illegal() -> dict[str, str]:
        return {"status": "nope"}

    with pytest.raises(ProductRouteConflict, match="protected_route_prefix"):
        registry.validate_product_routes("novafleet", (protected,))


def test_worker_registry_and_supervisor_manage_worker_lifecycle() -> None:
    registry = WorkerRegistry()
    worker = WorkerDefinition(
        name="fleet-worker",
        product_code="novafleet",
        handler=lambda context: None,
        queue="novafleet.jobs",
        dead_letter_queue="novafleet.dlq",
    )
    registry.register(worker)
    supervisor = WorkerSupervisor(registry)

    started = asyncio.run(supervisor.start_product_workers("novafleet"))
    assert started.success is True
    assert supervisor.worker_health("novafleet", "fleet-worker")["state"] == "RUNNING"

    paused = asyncio.run(supervisor.pause_worker("novafleet", "fleet-worker"))
    assert paused.state == "PAUSED"

    resumed = asyncio.run(supervisor.resume_worker("novafleet", "fleet-worker"))
    assert resumed.state == "RUNNING"

    stopped = asyncio.run(supervisor.stop_product_workers("novafleet"))
    assert stopped.success is True
    assert supervisor.worker_health("novafleet", "fleet-worker")["state"] == "STOPPED"


def test_infrastructure_provisioning_and_rollback() -> None:
    provisioner = InfrastructureProvisioner()
    requirement = InfrastructureRequirement(
        id="novafleet-postgres",
        product_code="novafleet",
        kind=InfrastructureKind.POSTGRES_SCHEMA,
        name="novafleet",
        required=True,
        configuration={"schema": "novafleet"},
        desired_state="present",
        ownership="product",
        region="AU",
    )

    plan = asyncio.run(provisioner.plan(requirement))
    result = asyncio.run(provisioner.apply(plan))
    verified = asyncio.run(provisioner.verify(requirement))
    rollback = asyncio.run(provisioner.rollback(result))

    assert plan.product_code == "novafleet"
    assert result.success is True
    assert verified.success is True
    assert rollback.success is True

    bad_requirement = InfrastructureRequirement(
        id="bad-name",
        product_code="novafleet",
        kind=InfrastructureKind.POSTGRES_SCHEMA,
        name="BadName",
        required=True,
        configuration={},
        desired_state="present",
        ownership="product",
        region="AU",
    )
    with pytest.raises(Exception, match="invalid_infrastructure_name"):
        asyncio.run(provisioner.plan(bad_requirement))


def test_activation_state_machine_and_protected_config() -> None:
    validate_activation_transition(ActivationState.DRAFT, ActivationState.REGISTERED)
    assert ActivationState.APPROVED in ALLOWED_ACTIVATION_TRANSITIONS[ActivationState.REVIEW_REQUIRED]
    with pytest.raises(ProductActivationBlocked):
        validate_activation_transition(ActivationState.DRAFT, ActivationState.ACTIVE)

    with pytest.raises(ProtectedConfigurationViolation):
        validate_protected_configuration(
            {
                "authentication_required": False,
                "authorization_required": True,
                "tenant_isolation_enabled": True,
                "audit_enabled": True,
                "evidence_enabled": True,
                "tls_required": True,
                "event_signature_required": True,
                "secret_provider": "vault",
                "database_encryption_enabled": True,
                "production_debug_enabled": False,
                "allow_memory_fallback": False,
                "allow_unsigned_events": False,
                "allow_cross_tenant_queries": False,
            },
            environment="production",
        )


def test_activation_service_and_verifier() -> None:
    activation = ProductActivationService()
    approval = RuntimeApproval(
        approval_id="approval-1",
        product_code="novafleet",
        product_version="2026.07.0",
        environment="public-pilot",
        decision="APPROVED",
        approver_id="approver-1",
        approver_roles=("ADMIN",),
        approved_at="2026-07-16T00:00:00Z",
        expires_at=None,
        conditions=("synthetic verification complete",),
        evidence_refs=("evidence-1",),
        checksum="sha256:" + "1" * 64,
    )

    assessment = asyncio.run(activation.validate("novafleet", "2026.07.0", _context()))
    assert assessment.state == ActivationState.REVIEW_REQUIRED

    approved = asyncio.run(activation.approve("novafleet", approval))
    provisioned = asyncio.run(activation.provision("novafleet", approval.approval_id))
    loaded = asyncio.run(activation.load("novafleet", approval.approval_id))
    deployed = asyncio.run(activation.deploy("novafleet", approval.approval_id))
    verified = asyncio.run(activation.verify("novafleet", approval.approval_id))
    active = asyncio.run(activation.activate("novafleet", approval.approval_id))

    assert approved.current_state == ActivationState.APPROVED
    assert provisioned.current_state == ActivationState.PROVISIONING
    assert loaded.current_state == ActivationState.LOADING
    assert deployed.current_state == ActivationState.DEPLOYING
    assert verified.current_state == ActivationState.VERIFYING
    assert active.current_state == ActivationState.ACTIVE

    verifier = DeploymentVerifier()
    plan = verifier.plan("novafleet", "2026.07.0", "public-pilot", "AU")
    record = verifier.execute(plan)
    assert record.status == "PASS"
    assert verifier.latest("novafleet").plan_id == plan.plan_id
