from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Dict


@dataclass(frozen=True)
class ExecutionMetrics:
    execution_id: str
    duration_ms: float
    accepted: bool
    result_hash: str
    timestamp: float

    def to_dict(self) -> Dict[str, object]:
        return {
            "execution_id": self.execution_id,
            "duration_ms": self.duration_ms,
            "accepted": self.accepted,
            "result_hash": self.result_hash,
            "timestamp": self.timestamp,
        }


def build_execution_metrics(
    execution_id: str,
    duration_ms: float,
    accepted: bool,
    result_hash: str,
) -> ExecutionMetrics:
    return ExecutionMetrics(
        execution_id=execution_id,
        duration_ms=duration_ms,
        accepted=accepted,
        result_hash=result_hash,
        timestamp=time.time(),
    )
