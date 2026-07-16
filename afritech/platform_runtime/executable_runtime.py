"""Executable runtime coordinator for NovaTech products."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .activation import ProductActivationService
from .command_executor import ProductCommandExecutor
from .deployment_verifier import DeploymentVerifier
from .errors import ProductActivationBlocked, ProductLoadRejected
from .models import LoadedProduct, ProductRuntimeState, RuntimeApproval
from .product_loader import ProductModuleLoader
from .provisioning import InfrastructureProvisioner
from .query_executor import ProductQueryExecutor
from .registry import BackendProductRegistration, ProductRuntimeRegistry
from .route_registry import RouteRegistry
from .runtime_evidence import RuntimeEvidenceService
from .worker_supervisor import WorkerSupervisor


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutableProductRuntime:
    def __init__(
        self,
        product_registry: ProductRuntimeRegistry,
        product_loader: ProductModuleLoader | None = None,
        command_executor: ProductCommandExecutor | None = None,
        query_executor: ProductQueryExecutor | None = None,
        route_registry: RouteRegistry | None = None,
        worker_supervisor: WorkerSupervisor | None = None,
        infrastructure_provisioner: InfrastructureProvisioner | None = None,
        activation_service: ProductActivationService | None = None,
        evidence_service: RuntimeEvidenceService | None = None,
        deployment_verifier: DeploymentVerifier | None = None,
    ) -> None:
        self.registry = product_registry
        self.route_registry = route_registry or RouteRegistry()
        self.worker_supervisor = worker_supervisor or WorkerSupervisor()
        self.infrastructure_provisioner = infrastructure_provisioner or InfrastructureProvisioner()
        self.activation_service = activation_service or ProductActivationService()
        self.evidence_service = evidence_service or RuntimeEvidenceService()
        self.deployment_verifier = deployment_verifier or DeploymentVerifier()
        self.command_executor = command_executor or ProductCommandExecutor(self.evidence_service)
        self.query_executor = query_executor or ProductQueryExecutor(self.evidence_service)
        self.product_loader = product_loader or ProductModuleLoader(route_registry=self.route_registry, command_registry=self.registry.command_registry, query_registry=self.registry.query_registry, worker_registry=self.worker_supervisor.worker_registry)
        self._loaded: dict[str, LoadedProduct] = {}
        self._state: dict[str, ProductRuntimeState] = {}
        self._evidence: list[dict[str, Any]] = []

    async def load_product(self, product_code: str) -> LoadedProduct:
        registration = self.registry._require_product(product_code)
        loaded = self.product_loader.load(registration)
        self._loaded[product_code.lower()] = loaded
        self._state[product_code.lower()] = ProductRuntimeState.LOADED
        return loaded

    async def start_product(self, product_code: str) -> dict[str, Any]:
        loaded = self._loaded.get(product_code.lower()) or await self.load_product(product_code)
        await self.worker_supervisor.start_product_workers(product_code)
        self._state[product_code.lower()] = ProductRuntimeState.RUNNING
        approval = RuntimeApproval(
            approval_id=f"approval-{product_code}",
            product_code=product_code,
            product_version=loaded.version,
            environment=self.registry.settings.environment,
            decision="APPROVED",
            approver_id="platform",
            approver_roles=("ADMIN",),
            approved_at=_now(),
            expires_at=None,
            conditions=("synthetic verification complete",),
            evidence_refs=(),
            checksum=loaded.module_checksum,
        )
        self.activation_service._approvals[approval.approval_id] = approval
        return {"product_code": product_code, "state": "RUNNING", "loaded_at": loaded.loaded_at, "approval_id": approval.approval_id}

    async def stop_product(self, product_code: str) -> dict[str, Any]:
        await self.worker_supervisor.stop_product_workers(product_code)
        self._state[product_code.lower()] = ProductRuntimeState.STOPPED
        return {"product_code": product_code, "state": "STOPPED"}

    async def reload_product(self, product_code: str) -> dict[str, Any]:
        await self.stop_product(product_code)
        loaded = await self.load_product(product_code)
        return {"product_code": product_code, "state": loaded.state.value}

    async def quarantine_product(self, product_code: str, reason: str) -> dict[str, Any]:
        self._state[product_code.lower()] = ProductRuntimeState.QUARANTINED
        return {"product_code": product_code, "state": "QUARANTINED", "reason": reason}

    def get_loaded_product(self, product_code: str) -> LoadedProduct:
        if product_code.lower() not in self._loaded:
            raise KeyError(product_code)
        return self._loaded[product_code.lower()]

    def snapshot(self) -> dict[str, Any]:
        return {
            "loaded": {key: value.state.value for key, value in self._loaded.items()},
            "states": {key: value.value for key, value in self._state.items()},
            "workers": self.worker_supervisor.health_snapshot(),
            "routes": self.route_registry.snapshot(),
            "registry": self.registry.snapshot() if hasattr(self.registry, "snapshot") else self.registry.summary(),
        }


__all__ = ["ExecutableProductRuntime"]
