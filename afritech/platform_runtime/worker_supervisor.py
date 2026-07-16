"""Worker supervision for NovaTech product runtimes."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .models import WorkerDefinition, WorkerHealthRecord, WorkerOperationResult, WorkerState
from .worker_registry import WorkerRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class _WorkerRuntimeState:
    definition: WorkerDefinition
    state: WorkerState = WorkerState.REGISTERED
    replica_id: str = "local"
    started_at: str = ""
    last_heartbeat_at: str = ""
    last_success_at: str = ""
    last_failure_at: str = ""
    processed_count: int = 0
    failure_count: int = 0
    retry_count: int = 0
    dead_letter_count: int = 0
    current_job_id: str | None = None
    consumer_lag: int = 0

    def health(self) -> WorkerHealthRecord:
        return WorkerHealthRecord(
            product_code=self.definition.product_code,
            worker_name=self.definition.name,
            state=self.state,
            replica_id=self.replica_id,
            started_at=self.started_at,
            last_heartbeat_at=self.last_heartbeat_at,
            last_success_at=self.last_success_at,
            last_failure_at=self.last_failure_at,
            processed_count=self.processed_count,
            failure_count=self.failure_count,
            retry_count=self.retry_count,
            dead_letter_count=self.dead_letter_count,
            current_job_id=self.current_job_id,
            consumer_lag=self.consumer_lag,
        )


class WorkerSupervisor:
    def __init__(self, worker_registry: WorkerRegistry | None = None) -> None:
        self.worker_registry = worker_registry or WorkerRegistry()
        self._state: dict[tuple[str, str], _WorkerRuntimeState] = {}

    async def start_product_workers(self, product_code: str) -> WorkerOperationResult:
        workers = self.worker_registry.list_product_workers(product_code)
        for worker in workers:
            state = self._state.setdefault((worker.product_code.lower(), worker.name.lower()), _WorkerRuntimeState(worker))
            state.state = WorkerState.STARTING
            state.started_at = state.started_at or _now()
            state.last_heartbeat_at = _now()
            state.state = WorkerState.RUNNING
        return WorkerOperationResult(product_code=product_code, operation="start", success=True, state="RUNNING", evidence_id=f"worker-{product_code}-start", details={"workers": [worker.name for worker in workers]})

    async def stop_product_workers(self, product_code: str, *, drain: bool = True) -> WorkerOperationResult:
        workers = self.worker_registry.list_product_workers(product_code)
        for worker in workers:
            state = self._state.setdefault((worker.product_code.lower(), worker.name.lower()), _WorkerRuntimeState(worker))
            state.state = WorkerState.DRAINING if drain else WorkerState.STOPPING
            state.state = WorkerState.STOPPED
        return WorkerOperationResult(product_code=product_code, operation="stop", success=True, state="STOPPED", evidence_id=f"worker-{product_code}-stop", details={"drain": drain})

    async def restart_worker(self, product_code: str, worker_name: str) -> WorkerOperationResult:
        worker = self.worker_registry.get(product_code, worker_name)
        state = self._state.setdefault((worker.product_code.lower(), worker.name.lower()), _WorkerRuntimeState(worker))
        state.state = WorkerState.STARTING
        state.last_heartbeat_at = _now()
        state.state = WorkerState.RUNNING
        return WorkerOperationResult(product_code=product_code, operation="restart", success=True, state="RUNNING", evidence_id=f"worker-{product_code}-{worker_name}-restart", details={})

    async def pause_worker(self, product_code: str, worker_name: str) -> WorkerOperationResult:
        worker = self.worker_registry.get(product_code, worker_name)
        state = self._state.setdefault((worker.product_code.lower(), worker.name.lower()), _WorkerRuntimeState(worker))
        state.state = WorkerState.PAUSED
        return WorkerOperationResult(product_code=product_code, operation="pause", success=True, state="PAUSED", evidence_id=f"worker-{product_code}-{worker_name}-pause", details={})

    async def resume_worker(self, product_code: str, worker_name: str) -> WorkerOperationResult:
        worker = self.worker_registry.get(product_code, worker_name)
        state = self._state.setdefault((worker.product_code.lower(), worker.name.lower()), _WorkerRuntimeState(worker))
        state.state = WorkerState.RUNNING
        return WorkerOperationResult(product_code=product_code, operation="resume", success=True, state="RUNNING", evidence_id=f"worker-{product_code}-{worker_name}-resume", details={})

    def health_snapshot(self) -> dict[str, Any]:
        return {
            "workers": [asdict(state.health()) for state in self._state.values()],
            "state": {f"{key[0]}:{key[1]}": asdict(state.health()) for key, state in self._state.items()},
        }

    def worker_health(self, product_code: str, worker_name: str) -> dict[str, Any]:
        state = self._state.get((product_code.lower(), worker_name.lower()))
        if state is None:
            worker = self.worker_registry.get(product_code, worker_name)
            state = _WorkerRuntimeState(worker)
        return asdict(state.health())


__all__ = ["WorkerSupervisor"]
