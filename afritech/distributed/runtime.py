from __future__ import annotations

from typing import List, Callable, Any, Dict, Optional

from afritech.runtime.kernel.execute import ExecutionContext
from afritech.distributed.node import SovereignNode
from afritech.distributed.consensus import ConsensusEngine
from afritech.epoch.epoch_snapshot import EpochSnapshot


class DistributedRuntime:
    """
    Distributed Sovereign Execution Runtime.

    Responsibilities:
    - Initialize and manage sovereign nodes
    - Coordinate distributed execution
    - Delegate consensus validation
    - Provide a single entrypoint for multi-node execution
    """

    def __init__(self, node_ids: List[str]) -> None:
        if not node_ids:
            raise ValueError("DistributedRuntime requires at least one node")

        # ✅ Create nodes
        self.nodes: List[SovereignNode] = [
            SovereignNode(node_id) for node_id in node_ids
        ]

        # ✅ Consensus layer
        self.consensus: ConsensusEngine = ConsensusEngine(self.nodes)

        # ✅ Runtime state
        self._last_epoch: Optional[int] = None

    # -----------------------------------------------------
    # Execute (primary entrypoint)
    # -----------------------------------------------------

    def execute(
        self,
        fn: Callable[[ExecutionContext], Any],
        epoch_snapshot: EpochSnapshot,
    ) -> Dict[str, Any]:
        """
        Execute a function across all sovereign nodes.

        Guarantees:
        - Each node executes independently
        - Consensus enforced on results
        - Deterministic output required
        """

        if not callable(fn):
            raise TypeError("Execution requires a callable function")

        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise TypeError("Invalid EpochSnapshot provided")

        # ✅ Validate epoch transition
        self._validate_epoch(epoch_snapshot)

        # ✅ Delegate execution to consensus engine
        result = self.consensus.execute(fn, epoch_snapshot)

        # ✅ Update runtime state
        self._last_epoch = epoch_snapshot.semantic_epoch.number

        return result

    # -----------------------------------------------------
    # Batch execution (optional advanced)
    # -----------------------------------------------------

    def execute_batch(
        self,
        functions: List[Callable[[ExecutionContext], Any]],
        epoch_snapshot: EpochSnapshot,
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple functions sequentially across nodes.
        """

        results: List[Dict[str, Any]] = []

        for fn in functions:
            result = self.execute(fn, epoch_snapshot)
            results.append(result)

        return results

    # -----------------------------------------------------
    # Node management
    # -----------------------------------------------------

    def get_node_ids(self) -> List[str]:
        return [node.get_node_id() for node in self.nodes]

    def add_node(self, node_id: str) -> None:
        """
        Dynamically add a node to the network.
        """
        new_node = SovereignNode(node_id)
        self.nodes.append(new_node)

        # ✅ Rebuild consensus engine
        self.consensus = ConsensusEngine(self.nodes)

    def remove_node(self, node_id: str) -> None:
        """
        Remove a node from the network.
        """
        self.nodes = [n for n in self.nodes if n.get_node_id() != node_id]

        if not self.nodes:
            raise RuntimeError("Cannot remove all nodes")

        # ✅ Rebuild consensus engine
        self.consensus = ConsensusEngine(self.nodes)

    # -----------------------------------------------------
    # Internal validation
    # -----------------------------------------------------

    def _validate_epoch(self, epoch_snapshot: EpochSnapshot) -> None:
        """
        Ensure valid epoch progression across distributed system.
        """

        current = self._last_epoch
        incoming = epoch_snapshot.semantic_epoch.number

        if current is None:
            return

        if incoming < current:
            raise RuntimeError(
                f"Invalid epoch transition: {incoming} < {current}"
            )

    # -----------------------------------------------------
    # State inspection
    # -----------------------------------------------------

    def get_current_epoch(self) -> Optional[int]:
        return self._last_epoch

    def reset(self) -> None:
        """
        Reset all nodes in the distributed system.
        """

        for node in self.nodes:
            node.reset()

        self._last_epoch = None
