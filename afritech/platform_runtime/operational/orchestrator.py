"""Operational orchestration service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..adapters.base import AdapterExecutionMode
from ..models import InfrastructureRequirement
from ..persistence.models import InfrastructurePlanRecord
from ..persistence.repository import RuntimeControlRepository
from .activation_certificate import ActivationCertificate, build_activation_certificate
from .evidence_store import PersistentEvidenceStore
from .probes import VerificationContext
from .restart_recovery import RecoveryResult, RecoveryRunner
from .rollback import RollbackCoordinator, RollbackResult
from .verification import RuntimeVerificationService, VerificationRun


@dataclass
class OperationalRuntimeOrchestrator:
    repository: RuntimeControlRepository
    evidence_store: PersistentEvidenceStore
    verifier: RuntimeVerificationService
    recovery_runner: RecoveryRunner
    rollback_coordinator: RollbackCoordinator
    adapter_modes: dict[str, AdapterExecutionMode]

    async def provision_product(self, requirement: InfrastructureRequirement) -> dict[str, Any]:
        adapter_name = "postgres"
        if self.adapter_modes:
            adapter_name = next(iter(self.adapter_modes.keys()))
        record = InfrastructurePlanRecord(
            id=f"{requirement.product_code}:{requirement.id}",
            product_code=requirement.product_code,
            product_version="unknown",
            environment="unknown",
            region=requirement.region,
            tenant_id="",
            status="PLANNED",
            checksum=f"sha256:{requirement.id}",
            requirement_id=requirement.id,
            adapter=adapter_name,
            actions=({"operation": "PROVISION", "name": requirement.name},),
            created_by="system",
            updated_by="system",
        )
        await self.repository.save_infrastructure_plan(record)
        return {"status": "planned", "requirement_id": requirement.id}

    async def deploy_product(self, context: VerificationContext) -> dict[str, Any]:
        run = await self.verifier.run(context)
        return {"status": run.status, "verification_id": run.verification_id, "probe_results": [result.__dict__ for result in run.probe_results]}

    async def verify_product(self, context: VerificationContext) -> VerificationRun:
        return await self.verifier.run(context)

    async def recover_product(self, product_code: str, observed_state: dict[str, Any]) -> RecoveryResult:
        return await self.recovery_runner.recover(product_code, observed_state=observed_state)

    async def rollback_product(self, product_code: str, *, reason: str, deployment_id: str, previous_deployment_id: str) -> RollbackResult:
        return await self.rollback_coordinator.rollback(product_code, reason=reason, deployment_id=deployment_id, previous_deployment_id=previous_deployment_id)

    async def activate_product(self, product_code: str, *, evidence_payload: dict[str, Any], **certificate_kwargs: Any) -> ActivationCertificate:
        certificate_kwargs.setdefault("product_code", product_code)
        certificate = build_activation_certificate(evidence_payload=evidence_payload, **certificate_kwargs)
        await self.evidence_store.write(
            type(
                "Evidence",
                (),
                {
                    "environment": certificate.environment,
                    "region": certificate.region,
                    "product_code": certificate.product_code,
                    "version": certificate.product_version,
                    "evidence_id": f"{certificate.product_code}:{certificate.product_version}:activation",
                    "operation": "ACTIVATE",
                    "actor_id": certificate.approved_by,
                    "approval_id": "",
                    "correlation_id": certificate.evidence_root_hash[:16],
                    "signature": certificate.evidence_root_hash,
                    "recorded_at": certificate.activated_at,
                },
            )(),
            evidence_payload,
        )
        return certificate

    async def status(self, product_code: str) -> dict[str, Any]:
        return {
            "product_code": product_code,
            "deployments": [record.canonical_dict() for record in await self.repository.list_deployments(product_code)],
            "evidence": [record.canonical_dict() for record in await self.repository.list_evidence(product_code)],
            "rollback_runs": [record.canonical_dict() for record in await self.repository.list_rollback_runs(product_code)],
        }

    async def resources(self, product_code: str) -> dict[str, Any]:
        return {"product_code": product_code, "adapters": {key: value.value for key, value in self.adapter_modes.items()}}
