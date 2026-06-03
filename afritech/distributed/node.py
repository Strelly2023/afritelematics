from __future__ import annotations

from typing import Callable, Any, Dict

from afritech.runtime.runtime_engine import RuntimeEngine
from afritech.runtime.kernel.execute import ExecutionContext
from afritech.epoch.epoch_snapshot import EpochSnapshot


class SovereignNode:
    """
    Independent sovereign execution node.

    Responsibilities:
    - Maintain its own RuntimeEngine
    - Validate constitutional state
    - Execute functions under sovereign rules
    """

    def __init__(self, node_id: str) -> None:
        if not isinstance(node_id, str):
            raise TypeError("node_id must be a string")

        self.node_id: str = node_id
        self.engine: RuntimeEngine = RuntimeEngine()

        # ✅ internal state tracking
        self._last_validated_epoch: int | None = None

    # -----------------------------------------------------
    # Validation (pre-check)
    # -----------------------------------------------------

    def validate(self, epoch_snapshot: EpochSnapshot) -> bool:
        """
        Validate that this node can operate under the given epoch.

        Returns:
            True if valid, False otherwise
        """

        try:
            self.engine.initialize(epoch_snapshot)

            # ✅ track validated epoch
            self._last_validated_epoch = (
                epoch_snapshot.semantic_epoch.number
            )

            return True

        except Exception:
            self._last_validated_epoch = None
            return False

    # -----------------------------------------------------
    # Execution
    # -----------------------------------------------------

    def execute(
        self,
        fn: Callable[[ExecutionContext], Any],
        epoch_snapshot: EpochSnapshot,
    ) -> Dict[str, Any]:
        """
        Execute a function under sovereign control.

        Returns:
        {
            "node": str,
            "status": "accepted" | "rejected",
            "result": Any (if accepted),
            "error": str (if rejected)
        }
        """

        try:
            # ✅ ensure compatible epoch (auto-init if needed)
            if (
                self._last_validated_epoch
                != epoch_snapshot.semantic_epoch.number
            ):
                self.validate(epoch_snapshot)

            # ✅ execute using shared runtime engine
            result = self.engine.execute(fn, epoch_snapshot)

            return {
                "node": self.node_id,
                "status": "accepted",
                "result": result,
            }

        except Exception as e:
            return {
                "node": self.node_id,
                "status": "rejected",
                "error": str(e),
            }

    # -----------------------------------------------------
    # Status Helpers
    # -----------------------------------------------------

    def get_node_id(self) -> str:
        return self.node_id

    def get_last_epoch(self) -> int | None:
        return self._last_validated_epoch

    def reset(self) -> None:
        """
        Reset node state.
        """
        self.engine.reset()
        self._last_validated_epoch = None