from __future__ import annotations

from typing import List, Callable, Any, Dict
import time

from afritech.runtime.kernel.execute import ExecutionContext
from afritech.distributed.p2p.node import P2PNode
from afritech.distributed.verifier import ProofVerifier
from afritech.distributed.proof import validate_proof_structure
from afritech.epoch.epoch_snapshot import EpochSnapshot


class P2PNetwork:
    """
    Fully decentralized P2P execution network.

    Responsibilities:
    - Manage mesh of nodes
    - Trigger distributed execution
    - Collect proofs from nodes
    - Enforce zero-trust consensus
    """

    def __init__(self, node_ids: List[str]) -> None:
        if not node_ids:
            raise ValueError("P2PNetwork requires at least one node")

        # ✅ Initialize nodes
        self.nodes: List[P2PNode] = [P2PNode(n) for n in node_ids]

        # ✅ Fully connected mesh topology
        for node in self.nodes:
            for peer in self.nodes:
                if node != peer:
                    node.connect(peer)

        # ✅ Build public key registry
        self.public_keys: Dict[str, Any] = {
            node.node_id: node.zt_node.identity.public_key
            for node in self.nodes
        }

        # ✅ Zero-trust verifier
        self.verifier: ProofVerifier = ProofVerifier(self.public_keys)

    # -----------------------------------------------------
    # Execute across P2P network
    # -----------------------------------------------------

    def execute(
        self,
        fn: Callable[[ExecutionContext], Any],
        epoch_snapshot: EpochSnapshot,
        wait_time: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Execute distributed function across mesh.

        Flow:
        - Clear previous proofs
        - Inject EXECUTE message
        - Wait for gossip propagation
        - Collect proofs
        - Filter valid
        - Run consensus
        """

        if not callable(fn):
            raise TypeError("fn must be callable")

        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise TypeError("Invalid EpochSnapshot")

        # ✅ Clear previous proofs (CRITICAL)
        for node in self.nodes:
            node.clear_proofs()

        # ✅ Trigger execution from first node (leaderless injection)
        leader = self.nodes[0]
        leader.execute(fn, epoch_snapshot)

        # ✅ Allow gossip propagation
        time.sleep(wait_time)

        # ✅ Collect proofs
        proofs: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []

        for node in self.nodes:
            node_proofs = node.get_proofs()

            for proof in node_proofs:
                if not isinstance(proof, dict):
                    rejected.append({
                        "node": node.node_id,
                        "status": "rejected",
                        "error": "Invalid proof type"
                    })
                    continue

                if proof.get("status") == "rejected":
                    rejected.append(proof)
                    continue

                if not validate_proof_structure(proof):
                    rejected.append({
                        "node": node.node_id,
                        "status": "rejected",
                        "error": "Malformed proof"
                    })
                    continue

                proofs.append(proof)

        # ✅ Ensure proofs exist
        if not proofs:
            raise RuntimeError("No valid proofs collected")

        # ✅ Run zero-trust consensus
        consensus_result = self.verifier.consensus(proofs)

        # ✅ Return structured output
        return {
            "consensus": consensus_result,
            "valid_proofs": len(proofs),
            "rejected": rejected,
            "total_nodes": len(self.nodes),
        }

    # -----------------------------------------------------
    # Batch execution
    # -----------------------------------------------------

    def execute_batch(
        self,
        functions: List[Callable[[ExecutionContext], Any]],
        epoch_snapshot: EpochSnapshot,
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple functions across network.
        """

        results: List[Dict[str, Any]] = []

        for fn in functions:
            result = self.execute(fn, epoch_snapshot)
            results.append(result)

        return results

    # -----------------------------------------------------
    # Node utilities
    # -----------------------------------------------------

    def get_node_ids(self) -> List[str]:
        return [node.get_node_id() for node in self.nodes]

    def add_node(self, node_id: str) -> None:
        new_node = P2PNode(node_id)

        # connect to all existing nodes
        for node in self.nodes:
            node.connect(new_node)
            new_node.connect(node)

        self.nodes.append(new_node)

        # rebuild public keys + verifier
        self._rebuild_verifier()

    def remove_node(self, node_id: str) -> None:
        self.nodes = [n for n in self.nodes if n.get_node_id() != node_id]

        if not self.nodes:
            raise RuntimeError("Cannot remove all nodes")

        self._rebuild_verifier()

    def _rebuild_verifier(self) -> None:
        self.public_keys = {
            node.node_id: node.zt_node.identity.public_key
            for node in self.nodes
        }

        self.verifier = ProofVerifier(self.public_keys)

    # -----------------------------------------------------
    # Reset network
    # -----------------------------------------------------

    def reset(self) -> None:
        for node in self.nodes:
            node.reset()