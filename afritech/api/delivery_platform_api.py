"""Administrative API for the shared NovaTech delivery and optimisation platform."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.delivery_platform import (
    BuildDefinition,
    DeliveryPlatformOrchestrator,
    ProductDeploymentManifest,
)
from afritech.delivery_platform.build_orchestrator import BuildOrchestrator
from afritech.delivery_platform.deployment_planner import DeploymentPlanner
from afritech.delivery_platform.optimisation import OptimisationEngine
from afritech.delivery_platform.registry import DeliveryPlatformRegistry, build_default_delivery_platform_registry
from afritech.delivery_platform.verification import DeploymentVerificationEngine


class ServiceDeploymentPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str = Field(min_length=1)
    image: str = Field(min_length=1)
    port: int = 0
    replicas: dict[str, int] = Field(default_factory=dict)


class WorkerDeploymentPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str = Field(min_length=1)
    image: str = Field(min_length=1)
    queue: str = Field(min_length=1)
    replicas: dict[str, int] = Field(default_factory=dict)


class DeploymentManifestPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    product_code: str = Field(min_length=1)
    version: str = Field(min_length=1)
    owner: str = ""
    rollout_strategy: str = "rolling"
    rollback_policy: str = "automatic"
    supported_environments: list[str] = Field(default_factory=lambda: ["development", "staging", "production"])
    supported_regions: list[str] = Field(default_factory=lambda: ["AU"])
    services: list[ServiceDeploymentPayload] = Field(default_factory=list)
    workers: list[WorkerDeploymentPayload] = Field(default_factory=list)
    frontends: list[dict[str, Any]] = Field(default_factory=list)
    mobile_apps: list[dict[str, Any]] = Field(default_factory=list)
    infrastructure: list[dict[str, Any]] = Field(default_factory=list)
    migrations: list[dict[str, Any]] = Field(default_factory=list)
    scaling_policies: list[dict[str, Any]] = Field(default_factory=list)
    optimisation_policies: list[dict[str, Any]] = Field(default_factory=list)
    health_checks: list[dict[str, Any]] = Field(default_factory=list)
    verification_checks: list[dict[str, Any]] = Field(default_factory=list)


class BuildPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    build_id: str = Field(min_length=1)
    component_name: str = Field(min_length=1)
    build_profile: str = "node"
    source_path: str = Field(min_length=1)
    output_type: str = "artifact"
    dependency_lockfile: str = ""
    build_commands: list[str] = Field(default_factory=list)
    test_commands: list[str] = Field(default_factory=list)
    security_commands: list[str] = Field(default_factory=list)
    artifact_name: str = Field(min_length=1)
    artifact_version: str = Field(min_length=1)
    optimisation_profile: str = "default"


class DeployPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    environment: str = "staging"
    region: str = "AU"
    current_revision: str | None = None


class PromotionPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    deployment_id: str = Field(min_length=1)
    percent: int = 100


class RollbackPayload(BaseModel):
    model_config = ConfigDict(extra="allow")
    deployment_id: str = Field(min_length=1)
    reason: str = "rollback_requested"


def _manifest(payload: DeploymentManifestPayload) -> ProductDeploymentManifest:
    return ProductDeploymentManifest(
        product_code=payload.product_code,
        version=payload.version,
        owner=payload.owner,
        rollout_strategy=payload.rollout_strategy,
        rollback_policy=payload.rollback_policy,
        supported_environments=tuple(payload.supported_environments),
        supported_regions=tuple(payload.supported_regions),
        services=tuple(
            {
                "name": item.name,
                "image": item.image,
                "port": item.port,
                "replicas": item.replicas,
            }
            for item in payload.services
        ),
        workers=tuple(
            {
                "name": item.name,
                "image": item.image,
                "queue": item.queue,
                "replicas": item.replicas,
            }
            for item in payload.workers
        ),
        frontends=tuple(payload.frontends),
        mobile_apps=tuple(payload.mobile_apps),
        infrastructure=tuple(payload.infrastructure),
        migrations=tuple(payload.migrations),
        scaling_policies=tuple(
            {
                "policy_id": item.get("policy_id", f"{payload.product_code}:scaling:{index}"),
                "component": item.get("component", "service"),
                "minimum_replicas": int(item.get("minimum_replicas", 1)),
                "maximum_replicas": int(item.get("maximum_replicas", 1)),
                "signals": tuple(item.get("signals", [])),
            }
            for index, item in enumerate(payload.scaling_policies)
        ),
        optimisation_policies=tuple(
            {
                "policy_id": item.get("policy_id", f"{payload.product_code}:optimisation:{index}"),
                "product_code": payload.product_code,
                "component": item.get("component", "service"),
                "performance_budget": item.get("performance_budget", {}),
                "resource_budget": item.get("resource_budget", {}),
                "cost_budget": item.get("cost_budget", {}),
                "cache_profile": item.get("cache_profile", "standard-read"),
                "compression_profile": item.get("compression_profile", "default"),
                "scaling_profile": item.get("scaling_profile", "default"),
                "automatic_actions": tuple(item.get("automatic_actions", [])),
                "approval_required_actions": tuple(item.get("approval_required_actions", [])),
            }
            for index, item in enumerate(payload.optimisation_policies)
        ),
        health_checks=tuple(payload.health_checks),
        verification_checks=tuple(payload.verification_checks),
    )


def _orchestrator(registry: DeliveryPlatformRegistry | None = None) -> DeliveryPlatformOrchestrator:
    platform_registry = registry or build_default_delivery_platform_registry()
    return DeliveryPlatformOrchestrator(
        registry=platform_registry,
        builder=BuildOrchestrator(platform_registry),
        planner=DeploymentPlanner(),
        verifier=DeploymentVerificationEngine(),
        optimiser=OptimisationEngine(),
    )


def build_delivery_platform_router(registry: DeliveryPlatformRegistry | None = None) -> APIRouter:
    router = APIRouter(prefix="/v1/platform", tags=["delivery-platform"])
    orchestrator = _orchestrator(registry)

    @router.get("/deployments")
    def overview(_: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return orchestrator.snapshot()

    @router.get("/deployments/products")
    def list_products(_: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return {"products": [manifest.canonical_dict() for manifest in orchestrator.registry.list_manifests()]}

    @router.get("/deployments/products/{product_code}")
    def get_product(product_code: str, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        manifest = orchestrator.registry.get_manifest(product_code)
        if manifest is None:
            raise HTTPException(status_code=404, detail="unknown_product")
        return {
            "manifest": manifest.canonical_dict(),
            "artifacts": [artifact.canonical_dict() for artifact in orchestrator.registry.list_artifacts(product_code)],
            "deployments": [record.canonical_dict() for record in orchestrator.registry.list_deployments(product_code)],
            "verification_runs": [result.__dict__ for result in orchestrator.registry.list_verification_runs(product_code)],
            "optimisation": orchestrator.optimisation_plan(product_code),
        }

    @router.post("/deployments/products/{product_code}/validate")
    def validate_product(product_code: str, payload: DeploymentManifestPayload, _: Any = Depends(require_roles("ADMIN", "DEVELOPER"))) -> dict[str, Any]:
        if product_code != payload.product_code:
            raise HTTPException(status_code=400, detail="product_code_mismatch")
        manifest = orchestrator.register_product(_manifest(payload))
        return {"status": "VALIDATED", "manifest": manifest.canonical_dict()}

    @router.post("/deployments/products/{product_code}/build")
    def build_product(product_code: str, payload: BuildPayload, _: Any = Depends(require_roles("ADMIN", "DEVELOPER"))) -> dict[str, Any]:
        manifest = orchestrator.registry.get_manifest(product_code)
        if manifest is None:
            raise HTTPException(status_code=404, detail="unknown_product")
        artifact = orchestrator.build(
            BuildDefinition(
                build_id=payload.build_id,
                product_code=product_code,
                component_name=payload.component_name,
                build_profile=payload.build_profile,
                source_path=payload.source_path,
                output_type=payload.output_type,
                dependency_lockfile=payload.dependency_lockfile,
                build_commands=tuple(payload.build_commands),
                test_commands=tuple(payload.test_commands),
                security_commands=tuple(payload.security_commands),
                artifact_name=payload.artifact_name,
                artifact_version=payload.artifact_version,
                optimisation_profile=payload.optimisation_profile,
            )
        )
        return {"status": artifact.promotion_status, "artifact": artifact.canonical_dict()}

    @router.post("/deployments/products/{product_code}/plan")
    def plan_product(product_code: str, payload: DeployPayload, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        artifacts = orchestrator.registry.list_artifacts(product_code)
        if not artifacts:
            raise HTTPException(status_code=404, detail="artifact_not_found")
        current_revision = payload.current_revision
        plan = orchestrator.plan(product_code, artifacts[-1], environment=payload.environment, region=payload.region, current_revision=current_revision)
        return {"status": "PLANNED", "plan": plan}

    @router.post("/deployments/products/{product_code}/approve")
    def approve_product(product_code: str, payload: dict[str, Any], _: Any = Depends(require_roles("ADMIN", "OPERATOR"))) -> dict[str, Any]:
        plan = orchestrator.registry.get_plan(str(payload.get("deployment_id", "")))
        if plan is None or plan["product_code"] != product_code:
            raise HTTPException(status_code=404, detail="unknown_deployment")
        plan["approval_id"] = str(payload.get("approval_id", "approval-required"))
        plan["requires_approval"] = False
        orchestrator.registry.save_plan(plan)
        return {"status": "APPROVED", "deployment_id": plan["deployment_id"], "approval_id": plan["approval_id"]}

    @router.post("/deployments/products/{product_code}/deploy")
    def deploy_product(product_code: str, payload: dict[str, Any], _: Any = Depends(require_roles("ADMIN", "OPERATOR", "RELEASE_MANAGER"))) -> dict[str, Any]:
        deployment_id = str(payload.get("deployment_id", ""))
        if not deployment_id:
            raise HTTPException(status_code=400, detail="deployment_id_required")
        return {"status": "DEPLOYED", "deployment": orchestrator.deploy(product_code, deployment_id)}

    @router.post("/deployments/products/{product_code}/verify")
    def verify_product(product_code: str, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "VERIFIER"))) -> dict[str, Any]:
        return orchestrator.verify(product_code)

    @router.post("/deployments/products/{product_code}/promote")
    def promote_product(product_code: str, payload: PromotionPayload, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "RELEASE_MANAGER"))) -> dict[str, Any]:
        return orchestrator.promote(product_code, payload.deployment_id, payload.percent)

    @router.post("/deployments/products/{product_code}/rollback")
    def rollback_product(product_code: str, payload: RollbackPayload, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "RELEASE_MANAGER"))) -> dict[str, Any]:
        return {"status": "ROLLED_BACK", "deployment": orchestrator.rollback(product_code, payload.deployment_id, payload.reason)}

    @router.get("/optimisation")
    def optimisation_overview(_: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return orchestrator.snapshot()

    @router.get("/optimisation/products/{product_code}")
    def optimisation_product(product_code: str, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER", "VERIFIER"))) -> dict[str, Any]:
        return {"product_code": product_code, "optimisation": orchestrator.optimisation_plan(product_code), "deployments": [record.canonical_dict() for record in orchestrator.registry.list_deployments(product_code)]}

    @router.post("/optimisation/products/{product_code}/analyse")
    def analyse(product_code: str, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        return orchestrator.analyse_optimisation(product_code)

    @router.post("/optimisation/products/{product_code}/plan")
    def plan(product_code: str, _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        plan = orchestrator.optimisation_plan(product_code) or orchestrator.analyse_optimisation(product_code)
        return {"status": "PLANNED", "optimisation": plan}

    @router.post("/optimisation/products/{product_code}/apply")
    def apply(product_code: str, payload: dict[str, Any], _: Any = Depends(require_roles("ADMIN", "OPERATOR", "DEVELOPER"))) -> dict[str, Any]:
        plan = orchestrator.optimisation_plan(product_code)
        if plan is None:
            raise HTTPException(status_code=404, detail="optimisation_plan_missing")
        applied = {**plan, "status": "APPLIED", "applied_at": "now", "notes": payload.get("notes", "")}
        orchestrator.registry.save_optimisation_plan(product_code, applied)
        return applied

    return router


__all__ = ["build_delivery_platform_router"]
