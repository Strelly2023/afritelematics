"""Executable runtime API surfaces for NovaTech product runtimes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.platform_runtime.activation import ProductActivationService
from afritech.platform_runtime.command_executor import ProductCommandExecutor
from afritech.platform_runtime.deployment_verifier import DeploymentVerifier
from afritech.platform_runtime.executable_runtime import ExecutableProductRuntime
from afritech.platform_runtime.models import ExecutionContext, RuntimeApproval
from afritech.platform_runtime.provisioning import InfrastructureProvisioner
from afritech.platform_runtime.registry import ProductRuntimeRegistry, build_default_product_runtime_registry
from afritech.platform_runtime.route_registry import RouteRegistry
from afritech.platform_runtime.runtime_evidence import RuntimeEvidenceService
from afritech.platform_runtime.worker_supervisor import WorkerSupervisor


class CommandExecutionPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    payload: dict[str, Any] = Field(default_factory=dict)
    purpose: str = ""
    idempotency_key: str | None = None


class QueryExecutionPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    parameters: dict[str, Any] = Field(default_factory=dict)
    purpose: str = ""


class RuntimeApprovalPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    approval_id: str = Field(min_length=1)
    product_version: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    decision: str = "APPROVED"
    approver_id: str = Field(min_length=1)
    approver_roles: list[str] = Field(default_factory=list)
    approved_at: str = ""
    expires_at: str | None = None
    conditions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    checksum: str = Field(min_length=1)


class RuntimeContextPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    request_id: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    causation_id: str | None = None
    tenant_id: str = Field(min_length=1)
    organization_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1)
    actor_type: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    region: str = Field(min_length=1)
    language: str = "en"
    timezone: str = "UTC"
    trace_id: str = Field(min_length=1)
    device_id: str | None = None
    session_id: str | None = None
    idempotency_key: str | None = None
    purpose: str = ""


def _runtime(runtime: ExecutableProductRuntime | None = None) -> ExecutableProductRuntime:
    if runtime is not None:
        return runtime
    registry = build_default_product_runtime_registry()
    return ExecutableProductRuntime(
        registry,
        route_registry=RouteRegistry(),
        worker_supervisor=WorkerSupervisor(),
        infrastructure_provisioner=InfrastructureProvisioner(),
        activation_service=ProductActivationService(),
        evidence_service=RuntimeEvidenceService(),
        command_executor=ProductCommandExecutor(),
        deployment_verifier=DeploymentVerifier(),
    )


def _context(product_code: str, payload: RuntimeContextPayload) -> ExecutionContext:
    return ExecutionContext(
        request_id=payload.request_id,
        correlation_id=payload.correlation_id,
        causation_id=payload.causation_id,
        product_code=product_code,
        tenant_id=payload.tenant_id,
        organization_id=payload.organization_id,
        actor_id=payload.actor_id,
        actor_type=payload.actor_type,
        roles=(),
        permissions=(),
        environment=payload.environment,
        region=payload.region,
        language=payload.language,
        timezone=payload.timezone,
        trace_id=payload.trace_id,
        device_id=payload.device_id,
        session_id=payload.session_id,
        idempotency_key=payload.idempotency_key,
        purpose=payload.purpose,
    )


def build_executable_runtime_router(runtime: ExecutableProductRuntime | None = None) -> APIRouter:
    router = APIRouter(prefix="/v1/platform/runtime", tags=["platform-runtime-exec"])
    execution_runtime = _runtime(runtime)

    @router.get("")
    def snapshot(_: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return execution_runtime.snapshot()

    @router.post("/products/{product_code}/load")
    async def load_product(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        loaded = await execution_runtime.load_product(product_code)
        return {"product_code": loaded.product_code, "version": loaded.version, "state": loaded.state.value, "module_checksum": loaded.module_checksum}

    @router.post("/products/{product_code}/start")
    async def start_product(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return await execution_runtime.start_product(product_code)

    @router.post("/products/{product_code}/stop")
    async def stop_product(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return await execution_runtime.stop_product(product_code)

    @router.post("/products/{product_code}/reload")
    async def reload_product(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return await execution_runtime.reload_product(product_code)

    @router.post("/products/{product_code}/quarantine")
    async def quarantine_product(product_code: str, reason: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return await execution_runtime.quarantine_product(product_code, reason)

    @router.post("/products/{product_code}/commands/{command_name}")
    async def execute_command(product_code: str, command_name: str, payload: CommandExecutionPayload, context: RuntimeContextPayload, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        result = await execution_runtime.command_executor.execute(product_code=product_code, command_name=command_name, payload=payload.payload, context=_context(product_code, context), loaded_product=execution_runtime.get_loaded_product(product_code))
        return asdict(result)

    @router.post("/products/{product_code}/queries/{query_name}")
    async def execute_query(product_code: str, query_name: str, payload: QueryExecutionPayload, context: RuntimeContextPayload, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        result = await execution_runtime.query_executor.execute(product_code=product_code, query_name=query_name, parameters=payload.parameters, context=_context(product_code, context), loaded_product=execution_runtime.get_loaded_product(product_code))
        return asdict(result)

    @router.get("/products/{product_code}/workers")
    def list_workers(product_code: str) -> dict[str, Any]:
        return execution_runtime.worker_supervisor.worker_registry.snapshot()

    return router


__all__ = ["build_executable_runtime_router"]
