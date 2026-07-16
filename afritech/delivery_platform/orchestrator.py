"""Shared delivery orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .build_orchestrator import BuildOrchestrator
from .contracts import ArtifactRecord, BuildDefinition, DeliveryDeploymentRecord, ProductDeploymentManifest
from .deployment_planner import DeploymentPlanner
from .errors import DeploymentStateError, ManifestConflictError, NotConnectedError
from .optimisation import OptimisationEngine, OptimisationPlan
from .registry import DeliveryPlatformRegistry
from .verification import DeploymentVerificationEngine


@dataclass
class DeliveryPlatformOrchestrator:
    registry: DeliveryPlatformRegistry
    builder: BuildOrchestrator
    planner: DeploymentPlanner
    verifier: DeploymentVerificationEngine
    optimiser: OptimisationEngine

    def register_product(self, manifest: ProductDeploymentManifest) -> ProductDeploymentManifest:
        return self.registry.register_manifest(manifest)

    def build(self, definition: BuildDefinition) -> ArtifactRecord:
        return self.builder.build(definition)

    def plan(self, product_code: str, artifact: ArtifactRecord, *, environment: str, region: str, current_revision: str | None = None) -> dict[str, Any]:
        manifest = self.registry.get_manifest(product_code)
        if manifest is None:
          raise ManifestConflictError(f"unknown_product:{product_code}")
        plan = self.planner.plan(manifest, artifact, environment=environment, region=region, current_revision=current_revision)
        self.registry.save_plan(plan.canonical_dict())
        return plan.canonical_dict()

    def deploy(self, product_code: str, deployment_id: str) -> dict[str, Any]:
        plan = self.registry.get_plan(deployment_id)
        if plan is None:
            raise DeploymentStateError(f"unknown_deployment:{deployment_id}")
        artifacts = self.registry.list_artifacts(product_code)
        if not artifacts:
            raise NotConnectedError(f"no_artifact_for:{product_code}")
        artifact = artifacts[-1]
        record = DeliveryDeploymentRecord(
            deployment_id=deployment_id,
            product_code=product_code,
            version=plan["version"],
            environment=plan["environment"],
            region=plan["region"],
            revision=plan["proposed_revision"],
            artifact_id=artifact.artifact_id,
            artifact_checksum=artifact.artifact_checksum,
            current_state="DEPLOYED",
            strategy=plan.get("rollout_strategy", "rolling"),
            approval_id="approval-required" if plan.get("requires_approval") else "",
            rollback_target=plan.get("rollback_target"),
            metadata={"actions": plan.get("actions", []), "risks": plan.get("risks", [])},
        )
        self.registry.save_deployment(record)
        return record.canonical_dict()

    def verify(self, product_code: str) -> dict[str, Any]:
        manifest = self.registry.get_manifest(product_code)
        if manifest is None:
            raise ManifestConflictError(f"unknown_product:{product_code}")
        result = self.verifier.run(product_code, manifest.verification_checks or manifest.health_checks)
        for check in result["results"]:
            self.registry.save_verification(product_code, check)
        return {
            "verification_id": result["verification_id"],
            "status": result["status"],
            "results": [check.__dict__ for check in result["results"]],
        }

    def promote(self, product_code: str, deployment_id: str, percent: int = 100) -> dict[str, Any]:
        deployments = list(self.registry.list_deployments(product_code))
        if not deployments:
            raise DeploymentStateError(f"unknown_deployment:{deployment_id}")
        latest = deployments[-1]
        updated = DeliveryDeploymentRecord(**{**latest.canonical_dict(), "promoted_percent": max(0, min(100, percent)), "current_state": "ACTIVE"})
        deployments[-1] = updated
        self.registry.deployments[product_code] = deployments
        return updated.canonical_dict()

    def rollback(self, product_code: str, deployment_id: str, reason: str) -> dict[str, Any]:
        deployments = list(self.registry.list_deployments(product_code))
        if not deployments:
            raise DeploymentStateError(f"unknown_deployment:{deployment_id}")
        latest = deployments[-1]
        rolled = DeliveryDeploymentRecord(**{**latest.canonical_dict(), "current_state": "ROLLED_BACK", "metadata": {**dict(latest.metadata), "rollback_reason": reason}})
        deployments[-1] = rolled
        self.registry.deployments[product_code] = deployments
        return rolled.canonical_dict()

    def analyse_optimisation(self, product_code: str) -> dict[str, Any]:
        manifest = self.registry.get_manifest(product_code)
        if manifest is None:
            raise ManifestConflictError(f"unknown_product:{product_code}")
        artifact = self.registry.list_artifacts(product_code)[-1] if self.registry.list_artifacts(product_code) else None
        if artifact is None:
            raise NotConnectedError(f"no_artifact_for:{product_code}")
        policy = manifest.optimisation_policies[0] if manifest.optimisation_policies else None
        plan = self.optimiser.analyse(artifact, policy)
        self.registry.save_optimisation_plan(product_code, {"product_code": plan.product_code, "component": plan.component, "recommendations": [rec.__dict__ for rec in plan.recommendations], "analysis": plan.analysis})
        return {"product_code": plan.product_code, "component": plan.component, "recommendations": [rec.__dict__ for rec in plan.recommendations], "analysis": plan.analysis}

    def optimisation_plan(self, product_code: str) -> dict[str, Any] | None:
        return self.registry.get_optimisation_plan(product_code)

    def snapshot(self) -> dict[str, Any]:
        return self.registry.snapshot()

