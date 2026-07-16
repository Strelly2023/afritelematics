"""Deterministic deployment planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import hashlib
import json
import uuid

from .contracts import ArtifactRecord, DeploymentAction, DeploymentPlan, ProductDeploymentManifest


def _checksum(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _value(item: Any, key: str, fallback: Any = "") -> Any:
    if isinstance(item, dict):
        return item.get(key, fallback)
    return getattr(item, key, fallback)


@dataclass
class DeploymentPlanner:
    def plan(
        self,
        manifest: ProductDeploymentManifest,
        artifact: ArtifactRecord,
        *,
        environment: str,
        region: str,
        current_revision: str | None = None,
        rollback_target: str | None = None,
    ) -> DeploymentPlan:
        actions = [
            DeploymentAction("VALIDATE_ARTIFACT", artifact.artifact_id, {"checksum": artifact.artifact_checksum}),
            DeploymentAction("APPLY_CONFIGURATION", manifest.product_code, {"environment": environment, "region": region}),
        ]
        if manifest.services:
            actions.extend(
                DeploymentAction(
                    "DEPLOY_SERVICE",
                    _value(service, "name", "service"),
                    {
                        "image": _value(service, "image", ""),
                        "port": _value(service, "port", 0),
                        "replicas": dict(_value(service, "replicas", {})),
                    },
                )
                for service in manifest.services
            )
        if manifest.workers:
            actions.extend(
                DeploymentAction(
                    "DEPLOY_WORKER",
                    _value(worker, "name", "worker"),
                    {
                        "image": _value(worker, "image", ""),
                        "queue": _value(worker, "queue", ""),
                        "replicas": dict(_value(worker, "replicas", {})),
                    },
                )
                for worker in manifest.workers
            )
        if manifest.frontends:
            actions.extend(
                DeploymentAction("PUBLISH_FRONTEND", str(_value(frontend, "name", "frontend")), dict(frontend) if isinstance(frontend, dict) else {"value": str(frontend)})
                for frontend in manifest.frontends
            )
        if manifest.mobile_apps:
            actions.extend(
                DeploymentAction(
                    "PUBLISH_MOBILE",
                    _value(mobile, "application", "mobile"),
                    {
                        "package_id": _value(mobile, "package_id", ""),
                        "version": _value(mobile, "version_name", _value(mobile, "version", "")),
                    },
                )
                for mobile in manifest.mobile_apps
            )
        if manifest.migrations:
            actions.extend(
                DeploymentAction(
                    "APPLY_MIGRATION",
                    str(_value(migration, "id", "migration")),
                    dict(migration) if isinstance(migration, dict) else {"value": str(migration)},
                    destructive=bool(_value(migration, "destructive", False)),
                )
                for migration in manifest.migrations
            )

        requires_migration = bool(manifest.migrations)
        destructive_actions = tuple(action.target for action in actions if action.destructive)
        risks = []
        if manifest.workers and not manifest.services:
            risks.append("worker-only deployment requires external consumer health checks")
        if manifest.mobile_apps:
            risks.append("mobile rollout requires staged store promotion")
        if destructive_actions:
            risks.append("destructive migration actions present")
        plan = DeploymentPlan(
            deployment_id=f"deployment-{uuid.uuid4().hex[:12]}",
            product_code=manifest.product_code,
            version=manifest.version,
            environment=environment,
            region=region,
            current_revision=current_revision,
            proposed_revision=f"{manifest.product_code}:{manifest.version}:{artifact.artifact_checksum}",
            actions=tuple(actions),
            risks=tuple(risks),
            destructive_actions=destructive_actions,
            requires_restart=bool(manifest.services or manifest.workers),
            requires_migration=requires_migration,
            requires_approval=bool(manifest.mobile_apps or destructive_actions or manifest.optimisation_policies),
            configuration_checksum=_checksum({"product_code": manifest.product_code, "environment": environment, "region": region}),
            artifact_checksum=artifact.artifact_checksum,
            plan_checksum=_checksum({
                "product_code": manifest.product_code,
                "version": manifest.version,
                "environment": environment,
                "region": region,
                "actions": [action.operation + ":" + action.target for action in actions],
                "artifact": artifact.artifact_checksum,
            }),
            rollout_strategy=manifest.rollout_strategy,
            rollback_target=rollback_target or current_revision,
        )
        return plan
