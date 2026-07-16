"""Activation API for NovaTech executable product runtime."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.platform_runtime.activation import ProductActivationService
from afritech.platform_runtime.models import RuntimeApproval


class RuntimeApprovalPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    approval_id: str = Field(min_length=1)
    product_code: str = Field(min_length=1)
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


class RuntimeValidationPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    region: str = Field(min_length=1)


def _service(service: ProductActivationService | None = None) -> ProductActivationService:
    return service or ProductActivationService()


def build_runtime_activation_router(service: ProductActivationService | None = None) -> APIRouter:
    router = APIRouter(prefix="/v1/platform/runtime/activations", tags=["platform-runtime-activation"])
    activation = _service(service)

    @router.get("")
    def list_activations(_: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return activation.snapshot()

    @router.get("/{product_code}")
    def get_activation(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return {"product_code": product_code, **activation.snapshot()}

    @router.post("/{product_code}/validate")
    async def validate(product_code: str, payload: RuntimeValidationPayload, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return asdict(await activation.validate(product_code, payload.version, payload))

    @router.post("/{product_code}/approve")
    async def approve(product_code: str, payload: RuntimeApprovalPayload, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        data = payload.model_dump()
        data["approver_roles"] = tuple(data.get("approver_roles", []))
        data["conditions"] = tuple(data.get("conditions", []))
        data["evidence_refs"] = tuple(data.get("evidence_refs", []))
        result = await activation.approve(product_code, RuntimeApproval(**data))
        return asdict(result)

    @router.post("/{product_code}/provision")
    async def provision(product_code: str, approval_id: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return asdict(await activation.provision(product_code, approval_id))

    @router.post("/{product_code}/load")
    async def load(product_code: str, approval_id: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return asdict(await activation.load(product_code, approval_id))

    @router.post("/{product_code}/deploy")
    async def deploy(product_code: str, approval_id: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return asdict(await activation.deploy(product_code, approval_id))

    @router.post("/{product_code}/verify")
    async def verify(product_code: str, approval_id: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return asdict(await activation.verify(product_code, approval_id))

    @router.post("/{product_code}/activate")
    async def activate(product_code: str, approval_id: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return asdict(await activation.activate(product_code, approval_id))

    @router.post("/{product_code}/suspend")
    async def suspend(product_code: str, reason: str = "", _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return asdict(await activation.suspend(product_code, reason))

    @router.post("/{product_code}/rollback")
    async def rollback(product_code: str, reason: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return asdict(await activation.rollback(product_code, reason))

    @router.post("/{product_code}/retire")
    async def retire(product_code: str, reason: str = "", _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return asdict(await activation.retire(product_code, reason))

    return router


__all__ = ["build_runtime_activation_router"]
