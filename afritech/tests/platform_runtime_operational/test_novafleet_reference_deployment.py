from __future__ import annotations

import asyncio

from afritech.platform_runtime.adapters.base import AdapterExecutionMode
from afritech.platform_runtime.operational import OperationalRuntimeOrchestrator, PersistentEvidenceStore, RecoveryRunner, RollbackCoordinator, RuntimeVerificationService, VerificationContext
from afritech.platform_runtime.persistence import SQLiteRuntimeControlRepository
from afritech.platform_runtime.models import InfrastructureKind, InfrastructureRequirement


def test_novafleet_reference_deployment_records_evidence(tmp_path) -> None:
    repo = SQLiteRuntimeControlRepository(tmp_path / "runtime.sqlite3")
    orchestrator = OperationalRuntimeOrchestrator(
        repository=repo,
        evidence_store=PersistentEvidenceStore(repository=repo, object_root=tmp_path / "evidence"),
        verifier=RuntimeVerificationService(probes=()),
        recovery_runner=RecoveryRunner(),
        rollback_coordinator=RollbackCoordinator(),
        adapter_modes={"postgres": AdapterExecutionMode.REAL},
    )
    requirement = InfrastructureRequirement(
        id="req-novafleet-1",
        product_code="novafleet",
        kind=InfrastructureKind.POSTGRES_SCHEMA,
        name="novafleet",
        required=True,
        configuration={},
        desired_state="ready",
        ownership="novafleet",
        region="AU",
    )

    asyncio.run(orchestrator.provision_product(requirement))
    certificate = asyncio.run(
        orchestrator.activate_product(
            "novafleet",
            evidence_payload={"tenant_id": "tenant-a", "result": "ok"},
            product_version="2026.07.0",
            environment="staging",
            region="AU",
            approved_by="release-manager",
            image_digest="sha256:image",
            module_checksum="sha256:mod",
            configuration_checksum="sha256:cfg",
            infrastructure_checksum="sha256:inf",
            route_plan_checksum="sha256:route",
            migration_checksum="sha256:mig",
            verification_status="PASS",
            restart_recovery_status="RECOVERED",
            rollback_status="PASS",
        )
    )
    status = asyncio.run(orchestrator.status("novafleet"))

    assert certificate.product_code == "novafleet"
    assert certificate.status == "ACTIVE"
    assert status["evidence"]
