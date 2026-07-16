"""Deployment and optimisation contracts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class ServiceDeploymentDefinition:
    name: str
    image: str
    port: int = 0
    replicas: Mapping[str, int] = field(default_factory=dict)
    environment: str = "production"
    region: str = "AU"
    health_path: str = "/health"
    readiness_path: str = "/health/ready"
    liveness_path: str = "/health/live"
    resource_profile: str = "standard-api"
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class WorkerDeploymentDefinition:
    name: str
    image: str
    queue: str
    replicas: Mapping[str, int] = field(default_factory=dict)
    concurrency: int = 1
    graceful_shutdown_seconds: int = 30
    heartbeat_seconds: int = 15
    resource_profile: str = "worker"
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class ScheduledJobDefinition:
    name: str
    schedule: str
    command: str
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class MobileDeploymentDefinition:
    application: str
    package_id: str
    version_name: str
    version_code: int
    artifact_uri: str
    minimum_supported_version: str
    region: str = "AU"


@dataclass(frozen=True, slots=True)
class ResourceProfile:
    profile_id: str
    cpu_request: str
    cpu_limit: str
    memory_request: str
    memory_limit: str
    minimum_replicas: int
    maximum_replicas: int
    concurrency_limit: int
    startup_timeout_seconds: int
    shutdown_timeout_seconds: int


@dataclass(frozen=True, slots=True)
class ScalingPolicy:
    policy_id: str
    component: str
    minimum_replicas: int
    maximum_replicas: int
    signals: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class OptimisationPolicy:
    policy_id: str
    product_code: str
    component: str
    performance_budget: Mapping[str, float] = field(default_factory=dict)
    resource_budget: Mapping[str, float] = field(default_factory=dict)
    cost_budget: Mapping[str, float] = field(default_factory=dict)
    cache_profile: str = "standard-read"
    compression_profile: str = "default"
    scaling_profile: str = "default"
    automatic_actions: tuple[str, ...] = ()
    approval_required_actions: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DeploymentVerificationCheck:
    check_id: str
    product_code: str
    category: str
    required: bool = True
    timeout_seconds: int = 10
    attempts: int = 1
    configuration: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DeploymentAction:
    operation: str
    target: str
    details: Mapping[str, Any] = field(default_factory=dict)
    destructive: bool = False


@dataclass(frozen=True, slots=True)
class DeploymentEnvironment:
    environment_id: str
    name: str
    classification: str
    production_like: bool
    regions: tuple[str, ...]
    deployment_adapter: str
    database_profile: str
    cache_profile: str
    event_profile: str
    storage_profile: str
    approval_policy: str
    verification_policy: str
    rollback_policy: str


@dataclass(frozen=True, slots=True)
class ProductDeploymentManifest:
    product_code: str
    version: str
    services: tuple[ServiceDeploymentDefinition, ...] = ()
    workers: tuple[WorkerDeploymentDefinition, ...] = ()
    jobs: tuple[ScheduledJobDefinition, ...] = ()
    frontends: tuple[dict[str, Any], ...] = ()
    mobile_apps: tuple[MobileDeploymentDefinition, ...] = ()
    infrastructure: tuple[dict[str, Any], ...] = ()
    migrations: tuple[dict[str, Any], ...] = ()
    scaling_policies: tuple[ScalingPolicy, ...] = ()
    optimisation_policies: tuple[OptimisationPolicy, ...] = ()
    health_checks: tuple[DeploymentVerificationCheck, ...] = ()
    verification_checks: tuple[DeploymentVerificationCheck, ...] = ()
    rollout_strategy: str = "rolling"
    rollback_policy: str = "automatic"
    supported_environments: tuple[str, ...] = ("development", "staging", "public-pilot", "production")
    supported_regions: tuple[str, ...] = ("AU",)
    owner: str = ""

    def canonical_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BuildDefinition:
    build_id: str
    product_code: str
    component_name: str
    build_profile: str
    source_path: str
    output_type: str
    dependency_lockfile: str
    build_commands: tuple[str, ...]
    test_commands: tuple[str, ...]
    security_commands: tuple[str, ...]
    artifact_name: str
    artifact_version: str
    optimisation_profile: str


@dataclass(frozen=True, slots=True)
class ArtifactRecord:
    artifact_id: str
    product_code: str
    component_name: str
    version: str
    git_commit: str
    build_number: str
    artifact_uri: str
    artifact_checksum: str
    image_digest: str = ""
    bundle_size_bytes: int = 0
    build_environment: str = ""
    security_scan: str = "PENDING"
    test_result: str = "PENDING"
    sbom_format: str = "CycloneDX"
    promotion_status: str = "BUILDING"
    created_at: str = field(default_factory=_now)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def canonical_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DeploymentPlan:
    deployment_id: str
    product_code: str
    version: str
    environment: str
    region: str
    current_revision: str | None
    proposed_revision: str
    actions: tuple[DeploymentAction, ...]
    risks: tuple[str, ...]
    destructive_actions: tuple[str, ...]
    requires_restart: bool
    requires_migration: bool
    requires_approval: bool
    configuration_checksum: str
    artifact_checksum: str
    plan_checksum: str
    rollout_strategy: str = "rolling"
    rollback_target: str | None = None

    def canonical_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class VerificationResult:
    check_id: str
    status: str
    started_at: str
    completed_at: str
    duration_ms: float
    evidence: Mapping[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class DeliveryDeploymentRecord:
    deployment_id: str
    product_code: str
    version: str
    environment: str
    region: str
    revision: str
    artifact_id: str
    artifact_checksum: str
    current_state: str
    strategy: str
    promoted_percent: int = 0
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    approval_id: str = ""
    verification_id: str = ""
    rollback_target: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def canonical_dict(self) -> dict[str, Any]:
        return asdict(self)

