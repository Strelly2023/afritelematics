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
    ✅ GA-Elite Fully Decentralized Sovereign Network
    """

    # =====================================================
    # ✅ INIT
    # =====================================================

    def __init__(self, node_ids: List[str]) -> None:
        if not node_ids:
            raise ValueError("At least one node required")

        self.nodes: List[P2PNode] = [P2PNode(n) for n in node_ids]

        # ✅ Full mesh connection
        for node in self.nodes:
            for peer in self.nodes:
                if node is not peer:
                    node.connect(peer)

        self._rebuild_verifier()

    # =====================================================
    # ✅ FUNCTION REGISTRATION
    # =====================================================

    def register_function(self, fn_id: str, fn: Callable) -> None:
        for node in self.nodes:
            node.register_function(fn_id, fn)

    # =====================================================
    # ✅ EXECUTE
    # =====================================================

    def execute(
        self,
        fn_id: str,
        epoch_snapshot: EpochSnapshot,
        args: Dict[str, Any] | None = None,
        wait_time: float = 0.2,
    ) -> Dict[str, Any]:

        if not isinstance(fn_id, str):
            raise TypeError("fn_id must be string")

        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise TypeError("Invalid EpochSnapshot")

        if args is None:
            args = {}

        # ✅ clear proofs
        for node in self.nodes:
            node.clear_proofs()

        # ✅ inject execution
        self.nodes[0].execute(fn_id, epoch_snapshot, args)

        # ✅ controlled wait (gossip settle)
        start = time.time()
        while time.time() - start < wait_time:
            pass  # deterministic wait loop

        # ✅ collect + deduplicate proofs
        proofs: Dict[str, Dict[str, Any]] = {}
        rejected: List[Dict[str, Any]] = []

        for node in self.nodes:

            for proof in node.get_proofs():

                if not isinstance(proof, dict):
                    rejected.append(self._reject(node, "Invalid proof type"))
                    continue

                if not validate_proof_structure(proof):
                    rejected.append(self._reject(node, "Malformed proof"))
                    continue

                if proof.get("status") == "rejected":
                    rejected.append(proof)
                    continue

                # ✅ deduplicate by proof hash or node
                proof_id = proof.get("hash") or str(proof)

                proofs[proof_id] = proof  # overwrite duplicates safely

        if not proofs:
            raise RuntimeError("No valid proofs collected")

        # ✅ consensus
        consensus_result = self.verifier.consensus(list(proofs.values()))

        return {
            "consensus": consensus_result,
            "valid_proofs": len(proofs),
            "rejected": rejected,
            "total_nodes": len(self.nodes),
        }

    # =====================================================
    # ✅ BATCH EXECUTION
    # =====================================================

    def execute_batch(
        self,
        fn_ids: List[str],
        epoch_snapshot: EpochSnapshot,
    ) -> List[Dict[str, Any]]:

        results = []

        for fn_id in fn_ids:
            results.append(self.execute(fn_id, epoch_snapshot))

        return results

    # =====================================================
    # ✅ NODE MANAGEMENT
    # =====================================================

    def get_node_ids(self) -> List[str]:
        return [node.get_node_id() for node in self.nodes]

    def add_node(self, node_id: str) -> None:
        new_node = P2PNode(node_id)

        for node in self.nodes:
            node.connect(new_node)
            new_node.connect(node)

        self.nodes.append(new_node)

        self._rebuild_verifier()

    def remove_node(self, node_id: str) -> None:
        self.nodes = [n for n in self.nodes if n.get_node_id() != node_id]

        if not self.nodes:
            raise RuntimeError("Cannot remove all nodes")

        self._rebuild_verifier()

    # =====================================================
    # ✅ VERIFIER REBUILD (SAFE)
    # =====================================================

    def _rebuild_verifier(self) -> None:

        self.public_keys = {
            node.get_node_id(): node._zt_node.identity.public_key
            for node in self.nodes
        }

        self.verifier = ProofVerifier(self.public_keys)

    # =====================================================
    # ✅ RESET
    # =====================================================

    def reset(self) -> None:
        for node in self.nodes:
            node.reset()

    # =====================================================
    # ✅ INTERNAL HELPERS
    # =====================================================

    def _reject(self, node: P2PNode, reason: str) -> Dict[str, Any]:
        return {
            "node": node.get_node_id(),
            "status": "rejected",
            "error": reason,
        }
