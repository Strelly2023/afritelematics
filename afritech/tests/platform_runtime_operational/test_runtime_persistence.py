from __future__ import annotations

import asyncio

from afritech.platform_runtime.persistence import (
    ActivationRecord,
    ApprovalRecord,
    EvidenceRecord,
    ProductVersionRecord,
    SQLiteRuntimeControlRepository,
)


def test_runtime_control_store_persists_records(tmp_path) -> None:
    repo = SQLiteRuntimeControlRepository(tmp_path / "runtime.sqlite3")
    product = ProductVersionRecord(
        id="novafleet:2026.07.0",
        product_code="novafleet",
        product_version="2026.07.0",
        environment="staging",
        region="AU",
        tenant_id="tenant-a",
        status="ACTIVE",
        checksum="sha256:1",
        module_checksum="sha256:mod",
        configuration_checksum="sha256:cfg",
        infrastructure_checksum="sha256:inf",
    )
    approval = ApprovalRecord(
        id="approval-1",
        product_code="novafleet",
        product_version="2026.07.0",
        environment="staging",
        region="AU",
        tenant_id="tenant-a",
        status="APPROVED",
        checksum="sha256:2",
        approval_type="runtime",
        approver_id="approver-1",
        approver_roles=("ADMIN",),
        evidence_refs=("evidence-1",),
        decision="APPROVED",
        conditions=("ok",),
    )
    activation = ActivationRecord(
        id="activation-1",
        product_code="novafleet",
        product_version="2026.07.0",
        environment="staging",
        region="AU",
        tenant_id="tenant-a",
        status="ACTIVE",
        checksum="sha256:3",
        approval_id="approval-1",
        current_state="ACTIVE",
        previous_state="VERIFYING",
        module_checksum="sha256:mod",
        configuration_checksum="sha256:cfg",
        infrastructure_checksum="sha256:inf",
        route_plan_checksum="sha256:route",
        migration_checksum="sha256:mig",
        details={"result": "ok"},
    )
    evidence = EvidenceRecord(
        id="evidence-1",
        product_code="novafleet",
        product_version="2026.07.0",
        environment="staging",
        region="AU",
        tenant_id="tenant-a",
        status="PERSISTED",
        checksum="sha256:4",
        evidence_id="evidence-1",
        operation="ACTIVATE",
        object_uri="file:///tmp/evidence-1.json",
        signature="sha256:sig",
        recorded_at="2026-07-16T00:00:00Z",
        metadata={"approval_id": "approval-1"},
    )

    asyncio.run(repo.save_product_version(product))
    asyncio.run(repo.save_approval(approval))
    asyncio.run(repo.save_activation(activation))
    asyncio.run(repo.save_evidence_record(evidence))

    reopened = SQLiteRuntimeControlRepository(tmp_path / "runtime.sqlite3")
    assert asyncio.run(reopened.get_product_version("novafleet", "2026.07.0")).checksum == "sha256:1"
    assert asyncio.run(reopened.get_approval("approval-1")).decision == "APPROVED"
    assert asyncio.run(reopened.get_activation("novafleet", "2026.07.0")).current_state == "ACTIVE"
    assert asyncio.run(reopened.list_evidence("novafleet"))[0].evidence_id == "evidence-1"

