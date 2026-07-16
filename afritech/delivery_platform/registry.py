"""In-memory governed delivery registry."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json

from .contracts import (
    ArtifactRecord,
    DeploymentEnvironment,
    DeliveryDeploymentRecord,
    ProductDeploymentManifest,
    VerificationResult,
)
from .errors import ManifestConflictError


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _validate_product_code(product_code: str) -> str:
    value = str(product_code or "").strip().lower()
    if not value or not value[0].isalpha() or not all(ch.isalnum() or ch == "_" or ch == "-" for ch in value):
        raise ManifestConflictError(f"invalid_product_code:{product_code}")
    return value


@dataclass
class DeliveryPlatformRegistry:
    manifests: dict[str, ProductDeploymentManifest] = field(default_factory=dict)
    artifacts: dict[str, list[ArtifactRecord]] = field(default_factory=dict)
    plans: dict[str, dict[str, Any]] = field(default_factory=dict)
    deployments: dict[str, list[DeliveryDeploymentRecord]] = field(default_factory=dict)
    verification_runs: dict[str, list[VerificationResult]] = field(default_factory=dict)
    environments: dict[str, DeploymentEnvironment] = field(default_factory=dict)
    optimisation_plans: dict[str, dict[str, Any]] = field(default_factory=dict)

    def register_environment(self, environment: DeploymentEnvironment) -> None:
        self.environments[environment.environment_id] = environment

    def register_manifest(self, manifest: ProductDeploymentManifest) -> ProductDeploymentManifest:
        product_code = _validate_product_code(manifest.product_code)
        normalized = ProductDeploymentManifest(**{**manifest.canonical_dict(), "product_code": product_code})
        self.manifests[product_code] = normalized
        return normalized

    def get_manifest(self, product_code: str) -> ProductDeploymentManifest | None:
        return self.manifests.get(_validate_product_code(product_code))

    def list_manifests(self) -> tuple[ProductDeploymentManifest, ...]:
        return tuple(self.manifests.values())

    def save_artifact(self, artifact: ArtifactRecord) -> ArtifactRecord:
        product_code = _validate_product_code(artifact.product_code)
        self.artifacts.setdefault(product_code, []).append(artifact)
        return artifact

    def list_artifacts(self, product_code: str) -> tuple[ArtifactRecord, ...]:
        return tuple(self.artifacts.get(_validate_product_code(product_code), []))

    def save_plan(self, plan: Mapping[str, Any]) -> Mapping[str, Any]:
        self.plans[str(plan["deployment_id"])] = dict(plan)
        return plan

    def get_plan(self, deployment_id: str) -> dict[str, Any] | None:
        plan = self.plans.get(deployment_id)
        return dict(plan) if plan else None

    def save_deployment(self, deployment: DeliveryDeploymentRecord) -> DeliveryDeploymentRecord:
        self.deployments.setdefault(_validate_product_code(deployment.product_code), []).append(deployment)
        return deployment

    def list_deployments(self, product_code: str) -> tuple[DeliveryDeploymentRecord, ...]:
        return tuple(self.deployments.get(_validate_product_code(product_code), []))

    def save_verification(self, product_code: str, result: VerificationResult) -> VerificationResult:
        self.verification_runs.setdefault(_validate_product_code(product_code), []).append(result)
        return result

    def list_verification_runs(self, product_code: str) -> tuple[VerificationResult, ...]:
        return tuple(self.verification_runs.get(_validate_product_code(product_code), []))

    def save_optimisation_plan(self, product_code: str, plan: Mapping[str, Any]) -> Mapping[str, Any]:
        key = _validate_product_code(product_code)
        self.optimisation_plans[key] = dict(plan)
        return plan

    def get_optimisation_plan(self, product_code: str) -> dict[str, Any] | None:
        plan = self.optimisation_plans.get(_validate_product_code(product_code))
        return dict(plan) if plan else None

    def snapshot(self) -> dict[str, Any]:
        return {
            "product_count": len(self.manifests),
            "deployment_count": sum(len(items) for items in self.deployments.values()),
            "artifact_count": sum(len(items) for items in self.artifacts.values()),
            "verification_count": sum(len(items) for items in self.verification_runs.values()),
            "environment_count": len(self.environments),
            "products": [
                {
                    "product_code": manifest.product_code,
                    "version": manifest.version,
                    "services": len(manifest.services),
                    "workers": len(manifest.workers),
                    "jobs": len(manifest.jobs),
                    "frontends": len(manifest.frontends),
                    "mobile_apps": len(manifest.mobile_apps),
                }
                for manifest in self.manifests.values()
            ],
            "environments": [environment.name for environment in self.environments.values()],
        }


def build_default_delivery_platform_registry() -> DeliveryPlatformRegistry:
    from .contracts import (
        ArtifactRecord,
        BuildDefinition,
        DeploymentAction,
        DeploymentEnvironment,
        DeploymentPlan,
        DeploymentVerificationCheck,
        MobileDeploymentDefinition,
        OptimisationPolicy,
        ProductDeploymentManifest,
        ResourceProfile,
        ScalingPolicy,
        ScheduledJobDefinition,
        ServiceDeploymentDefinition,
        WorkerDeploymentDefinition,
    )

    registry = DeliveryPlatformRegistry()
    for environment in (
        DeploymentEnvironment(
            environment_id="development",
            name="development",
            classification="internal",
            production_like=False,
            regions=("AU",),
            deployment_adapter="docker_compose",
            database_profile="dev",
            cache_profile="dev",
            event_profile="dev",
            storage_profile="dev",
            approval_policy="development",
            verification_policy="development",
            rollback_policy="development",
        ),
        DeploymentEnvironment(
            environment_id="staging",
            name="staging",
            classification="controlled",
            production_like=True,
            regions=("AU",),
            deployment_adapter="docker_compose",
            database_profile="staging",
            cache_profile="staging",
            event_profile="staging",
            storage_profile="staging",
            approval_policy="controlled",
            verification_policy="controlled",
            rollback_policy="controlled",
        ),
        DeploymentEnvironment(
            environment_id="production",
            name="production",
            classification="restricted",
            production_like=True,
            regions=("AU", "KE", "BI", "CD"),
            deployment_adapter="kubernetes",
            database_profile="production",
            cache_profile="production",
            event_profile="production",
            storage_profile="production",
            approval_policy="strict",
            verification_policy="strict",
            rollback_policy="strict",
        ),
    ):
        registry.register_environment(environment)

    registry.register_manifest(
        ProductDeploymentManifest(
            product_code="novacodepro",
            version="2026.07.0",
            services=(
                ServiceDeploymentDefinition(
                    name="novacodepro-portal",
                    image="registry.afritechnology.com/novacodepro-portal",
                    port=80,
                    replicas={"minimum": 2, "maximum": 6},
                    resource_profile="frontend",
                ),
            ),
            workers=(
                WorkerDeploymentDefinition(
                    name="novacodepro-agent-worker",
                    image="registry.afritechnology.com/novacodepro-worker",
                    queue="novacodepro.workflow",
                    replicas={"minimum": 1, "maximum": 4},
                ),
            ),
            jobs=(
                ScheduledJobDefinition(name="novacodepro-evidence-compaction", schedule="0 3 * * *", command="compact-evidence"),
            ),
            frontends=(
                {"name": "novacodepro-portal", "build_path": "novacodepro_portal", "hosting_profile": "static-cdn"},
            ),
            infrastructure=(
                {"kind": "object_storage_prefix", "name": "novacodepro/"},
            ),
            migrations=(),
            scaling_policies=(ScalingPolicy(policy_id="novacodepro-portal", component="portal", minimum_replicas=2, maximum_replicas=6),),
            optimisation_policies=(OptimisationPolicy(policy_id="novacodepro-portal", product_code="novacodepro", component="portal"),),
            health_checks=(
                DeploymentVerificationCheck(check_id="novacodepro:health", product_code="novacodepro", category="HTTP", configuration={"path": "/health"}),
            ),
            verification_checks=(
                DeploymentVerificationCheck(check_id="novacodepro:frontend", product_code="novacodepro", category="Frontend", configuration={"path": "/novacodepro/"}),
            ),
            supported_environments=("development", "staging", "production"),
            supported_regions=("AU",),
            owner="NovaCodePro Platform Team",
        )
    )
    registry.register_manifest(
        ProductDeploymentManifest(
            product_code="novafleet",
            version="2026.07.0",
            services=(
                ServiceDeploymentDefinition(
                    name="novafleet-api",
                    image="registry.afritechnology.com/novafleet-api",
                    port=8000,
                    replicas={"minimum": 2, "maximum": 8},
                    resource_profile="real-time-api",
                ),
            ),
            workers=(
                WorkerDeploymentDefinition(
                    name="novafleet-status-worker",
                    image="registry.afritechnology.com/novafleet-worker",
                    queue="novatech.fleet.events",
                    replicas={"minimum": 1, "maximum": 4},
                ),
            ),
            frontends=(
                {"name": "novafleet-portal", "build_path": "novacodepro_portal", "hosting_profile": "static-cdn"},
            ),
            mobile_apps=(
                MobileDeploymentDefinition(
                    application="driver",
                    package_id="com.novatech.novaride.driver",
                    version_name="2026.1.3",
                    version_code=6,
                    artifact_uri="s3://novatech-public-pilot/novafleet/driver.apk",
                    minimum_supported_version="2026.1.2",
                ),
            ),
            infrastructure=(
                {"kind": "postgres_schema", "name": "novafleet"},
                {"kind": "redis_namespace", "name": "novafleet"},
                {"kind": "event_stream", "name": "NOVATECH_FLEET"},
            ),
            scaling_policies=(ScalingPolicy(policy_id="novafleet-api", component="api", minimum_replicas=2, maximum_replicas=8),),
            optimisation_policies=(OptimisationPolicy(policy_id="novafleet-api", product_code="novafleet", component="api"),),
            health_checks=(
                DeploymentVerificationCheck(check_id="novafleet:api", product_code="novafleet", category="HTTP", configuration={"path": "/health"}),
            ),
            verification_checks=(
                DeploymentVerificationCheck(check_id="novafleet:worker", product_code="novafleet", category="Worker", configuration={"queue": "novatech.fleet.events"}),
            ),
            supported_environments=("staging", "production"),
            supported_regions=("AU",),
            owner="Fleet Platform Team",
        )
    )
    return registry
