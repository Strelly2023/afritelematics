"""Infrastructure provisioning API for NovaTech executable product runtime."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.platform_runtime.infrastructure import InfrastructureKind
from afritech.platform_runtime.models import InfrastructureRequirement
from afritech.platform_runtime.provisioning import InfrastructureProvisioner


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


def _service(service: InfrastructureProvisioner | None = None) -> InfrastructureProvisioner:
    return service or InfrastructureProvisioner()


def build_runtime_infrastructure_router(service: InfrastructureProvisioner | None = None) -> APIRouter:
    router = APIRouter(prefix="/v1/platform/runtime/infrastructure", tags=["platform-runtime-infrastructure"])
    provisioner = _service(service)

    @router.get("")
    def snapshot(_: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return provisioner.snapshot()

    @router.get("/{product_code}")
    def product_snapshot(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return {"product_code": product_code, **provisioner.snapshot()}

    @router.post("/{product_code}/plan")
    async def plan(product_code: str, payload: InfrastructureRequirementPayload, _: JWTClaims = Depends(require_roles("ADMIN", "PLATFORM_OPERATOR"))) -> dict[str, Any]:
        requirement = InfrastructureRequirement(**{**payload.model_dump(), "kind": InfrastructureKind(payload.kind)})
        return asdict(await provisioner.plan(requirement))

    @router.post("/{product_code}/provision")
    async def provision(product_code: str, payload: InfrastructureRequirementPayload, _: JWTClaims = Depends(require_roles("ADMIN", "PLATFORM_OPERATOR"))) -> dict[str, Any]:
        requirement = InfrastructureRequirement(**{**payload.model_dump(), "kind": InfrastructureKind(payload.kind)})
        plan = await provisioner.plan(requirement)
        return asdict(await provisioner.apply(plan))

    @router.post("/{product_code}/verify")
    async def verify(product_code: str, payload: InfrastructureRequirementPayload, _: JWTClaims = Depends(require_roles("ADMIN", "PLATFORM_OPERATOR"))) -> dict[str, Any]:
        requirement = InfrastructureRequirement(**{**payload.model_dump(), "kind": InfrastructureKind(payload.kind)})
        return asdict(await provisioner.verify(requirement))

    @router.post("/{product_code}/rollback")
    async def rollback(product_code: str, payload: InfrastructureRequirementPayload, _: JWTClaims = Depends(require_roles("ADMIN", "PLATFORM_OPERATOR"))) -> dict[str, Any]:
        requirement = InfrastructureRequirement(**{**payload.model_dump(), "kind": InfrastructureKind(payload.kind)})
        plan = await provisioner.plan(requirement)
        result = await provisioner.apply(plan)
        return asdict(await provisioner.rollback(result))

    return router


__all__ = ["build_runtime_infrastructure_router"]
