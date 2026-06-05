from __future__ import annotations

from typing import Any, Dict

from afritech.epoch.compiled.semantic_epoch import SemanticEpoch
from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.runtime.kernel.execute import ExecutionContext


class StateRebuilder:
    def rebuild_epoch(self, data: EpochSnapshot | Dict[str, Any]) -> EpochSnapshot:
        if isinstance(data, EpochSnapshot):
            return data

        if not isinstance(data, dict):
            raise TypeError("epoch data must be EpochSnapshot or dict")

        semantic = data.get("semantic_epoch")
        if not isinstance(semantic, dict):
            raise ValueError("missing semantic_epoch")

        epoch_hash = data.get("epoch_hash")
        if not isinstance(epoch_hash, str) or not epoch_hash:
            raise ValueError("missing epoch_hash")

        return EpochSnapshot(
            semantic_epoch=SemanticEpoch.from_dict(semantic),
            epoch_hash=epoch_hash,
        )

    def rebuild_context(self, data: EpochSnapshot | Dict[str, Any]) -> ExecutionContext:
        return ExecutionContext(self.rebuild_epoch(data))
