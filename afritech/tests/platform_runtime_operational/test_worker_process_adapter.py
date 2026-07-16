from __future__ import annotations

import asyncio

from afritech.platform_runtime.adapters.workers import LocalProcessWorkerAdapter, WorkerProcessSpec


def test_local_process_worker_adapter_starts_process() -> None:
    spec = WorkerProcessSpec(
        product_code="novafleet",
        worker_name="fleet-worker",
        command=("python", "-c", "print('ok')"),
        image=None,
        environment_refs=(),
        replicas=1,
        concurrency=1,
        timeout_seconds=30,
        restart_policy="never",
        health_endpoint=None,
        queue="novafleet.jobs",
    )
    result = asyncio.run(LocalProcessWorkerAdapter().start(spec))
    assert result["worker_name"] == "fleet-worker"
    assert result["mode"] == "REAL"

