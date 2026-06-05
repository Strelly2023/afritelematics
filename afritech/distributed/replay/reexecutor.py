from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping

from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.runtime.runtime_engine import RuntimeEngine


@dataclass(frozen=True)
class ReplayRequest:
    fn_id: str
    args: Dict[str, Any]
    epoch_snapshot: EpochSnapshot
    expected_result: Any
    expected_hash: str


class Reexecutor:
    def __init__(self, registry: Mapping[str, Callable]) -> None:
        self.registry = dict(registry)

    def reexecute(self, request: ReplayRequest) -> Any:
        fn = self.registry.get(request.fn_id)
        if not callable(fn):
            raise KeyError(f"function not registered: {request.fn_id}")

        engine = RuntimeEngine()
        return engine.execute(
            lambda ctx: fn(ctx, **request.args),
            request.epoch_snapshot,
            fn_id=request.fn_id,
        )
