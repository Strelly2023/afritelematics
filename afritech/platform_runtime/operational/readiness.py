"""Runtime readiness evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RuntimeReadinessSnapshot:
    status: str
    control_store: str
    adapters: dict[str, str]
    reconciliation: dict[str, Any]


def assess_runtime_readiness(*, control_store_ready: bool, adapters: dict[str, str], reconciliation_last_run_at: str = "") -> RuntimeReadinessSnapshot:
    status = "ready" if control_store_ready and all(value == "ready" for value in adapters.values()) else "degraded"
    return RuntimeReadinessSnapshot(status=status, control_store="ready" if control_store_ready else "unavailable", adapters=adapters, reconciliation={"status": "ready" if status == "ready" else "degraded", "last_run_at": reconciliation_last_run_at})

