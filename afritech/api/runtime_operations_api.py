"""Operational runtime API for NovaTech product runtimes."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.platform_runtime.adapters.base import AdapterExecutionMode
from afritech.platform_runtime.models import InfrastructureRequirement
from afritech.platform_runtime.operational import (
    OperationalRuntimeOrchestrator,
    PersistentEvidenceStore,
    RecoveryRunner,
    RollbackCoordinator,
    RuntimeVerificationService,
    VerificationContext,
    assess_runtime_readiness,
)
from afritech.platform_runtime.persistence.repository import build_runtime_control_repository


class InfrastructureRequirementPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    product_code: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    name: str = Field(min_length=1)
    required: bool = True
    configuration: dict[str, Any] = Field(default_factory=dict)
    desired_state: str = "present"
    ownership: str = "product"
    region: str = "AU"


class VerificationPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    base_url: str
    product_version: str
    environment: str
    region: str
    token: str | None = None
    tenant_id: str = ""
    approval_id: str = ""
    deployment_id: str = ""


class RecoveryPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    observed_state: dict[str, Any] = Field(default_factory=dict)


def _orchestrator(orchestrator: OperationalRuntimeOrchestrator | None = None) -> OperationalRuntimeOrchestrator:
    if orchestrator is not None:
        return orchestrator
    repository = build_runtime_control_repository(sqlite_path=Path("/tmp/novatech-runtime-control.sqlite3"))
    evidence_store = PersistentEvidenceStore(repository=repository, object_root=Path("/tmp/runtime-evidence"))
    return OperationalRuntimeOrchestrator(
        repository=repository,
        evidence_store=evidence_store,
        verifier=RuntimeVerificationService(),
        recovery_runner=RecoveryRunner(),
        rollback_coordinator=RollbackCoordinator(),
        adapter_modes={"postgres": AdapterExecutionMode.REAL, "redis": AdapterExecutionMode.REAL, "nats": AdapterExecutionMode.UNAVAILABLE, "object_storage": AdapterExecutionMode.REAL},
    )


def build_runtime_operations_router(orchestrator: OperationalRuntimeOrchestrator | None = None) -> APIRouter:
    router = APIRouter(prefix="/v1/platform/runtime/operations", tags=["platform-runtime-operations"])
    runtime = _orchestrator(orchestrator)

    @router.post("/{product_code}/provision")
    async def provision(product_code: str, payload: InfrastructureRequirementPayload, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "PLATFORM_OPERATOR"))) -> dict[str, Any]:
        requirement = InfrastructureRequirement(**{**payload.model_dump(), "kind": payload.kind})
        return await runtime.provision_product(requirement)

    @router.post("/{product_code}/deploy")
    async def deploy(product_code: str, payload: VerificationPayload, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "RELEASE_MANAGER"))) -> dict[str, Any]:
        return await runtime.deploy_product(VerificationContext(**payload.model_dump(), product_code=product_code))

    @router.post("/{product_code}/verify")
    async def verify(product_code: str, payload: VerificationPayload, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "VERIFIER"))) -> dict[str, Any]:
        return asdict(await runtime.verify_product(VerificationContext(**payload.model_dump(), product_code=product_code)))

    @router.post("/{product_code}/recover")
    async def recover(product_code: str, payload: RecoveryPayload, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR"))) -> dict[str, Any]:
        return asdict(await runtime.recover_product(product_code, payload.observed_state))

    @router.post("/{product_code}/rollback")
    async def rollback(product_code: str, payload: dict[str, Any], _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "RELEASE_MANAGER"))) -> dict[str, Any]:
        return asdict(await runtime.rollback_product(
            product_code,
            reason=str(payload.get("reason", "rollback_requested")),
            deployment_id=str(payload.get("deployment_id", "")),
            previous_deployment_id=str(payload.get("previous_deployment_id", "")),
        ))

    @router.get("/{product_code}/status")
    async def status(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return await runtime.status(product_code)

    @router.get("/{product_code}/resources")
    async def resources(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return await runtime.resources(product_code)

    @router.get("/{product_code}/deployments")
    async def deployments(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "VERIFIER"))) -> dict[str, Any]:
        return {"deployments": [record.canonical_dict() for record in await runtime.repository.list_deployments(product_code)]}

    @router.get("/{product_code}/evidence")
    async def evidence(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "VERIFIER", "AUDITOR"))) -> dict[str, Any]:
        return {"evidence": [record.canonical_dict() for record in await runtime.repository.list_evidence(product_code)]}

    return router


__all__ = ["build_runtime_operations_router"]
