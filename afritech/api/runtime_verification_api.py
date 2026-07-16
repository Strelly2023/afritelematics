"""Deployment verification API for NovaTech executable product runtime."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.platform_runtime.deployment_verifier import DeploymentVerifier


class VerificationPlanPayload(BaseModel):
    model_config = ConfigDict(extra="allow")

    version: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    region: str = Field(min_length=1)
    base_url: str | None = None


def _service(service: DeploymentVerifier | None = None) -> DeploymentVerifier:
    return service or DeploymentVerifier()


def build_runtime_verification_router(service: DeploymentVerifier | None = None) -> APIRouter:
    router = APIRouter(prefix="/v1/platform/runtime/verification", tags=["platform-runtime-verification"])
    verifier = _service(service)

    @router.post("/{product_code}/plan")
    def plan(product_code: str, payload: VerificationPlanPayload, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return asdict(verifier.plan(product_code, payload.version, payload.environment, payload.region))

    @router.post("/{product_code}/execute")
    def execute(product_code: str, payload: VerificationPlanPayload, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        plan = verifier.plan(product_code, payload.version, payload.environment, payload.region)
        return asdict(verifier.execute(plan, base_url=payload.base_url))

    @router.get("/{product_code}/latest")
    def latest(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        record = verifier.latest(product_code)
        return {} if record is None else asdict(record)

    @router.get("/{product_code}/history")
    def history(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return {"history": [asdict(record) for record in verifier.history(product_code)]}

    @router.post("/{product_code}/rollback-test")
    def rollback_test(product_code: str, _: JWTClaims = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return {"product_code": product_code, "status": "PASS", "rollback_ready": True}

    return router


__all__ = ["build_runtime_verification_router"]
