from __future__ import annotations

import asyncio
from pathlib import Path

from afritech.platform_runtime.operational.evidence_store import PersistentEvidenceStore
from afritech.platform_runtime.persistence import SQLiteRuntimeControlRepository
from afritech.platform_runtime.runtime_evidence import RuntimeEvidenceService


def test_evidence_persistence_writes_object_and_index(tmp_path) -> None:
    repo = SQLiteRuntimeControlRepository(tmp_path / "runtime.sqlite3")
    store = PersistentEvidenceStore(repository=repo, object_root=tmp_path / "evidence")
    evidence = RuntimeEvidenceService().record(
        product_code="novafleet",
        version="2026.07.0",
        environment="staging",
        region="AU",
        operation="ACTIVATE",
        actor_id="actor-a",
        approval_id="approval-1",
        correlation_id="corr-1",
        inputs={"a": 1},
        result={"b": 2},
        module_checksum="sha256:mod",
        configuration_checksum="sha256:cfg",
        infrastructure_checksum="sha256:inf",
    )
    uri = asyncio.run(store.write(evidence, {"tenant_id": "tenant-a", "result": "ok"}))
    assert uri.startswith("file:")
    assert Path(uri.replace("file://", "")).exists()

