from __future__ import annotations

from typing import List, Callable, Any, Dict

from afritech.runtime.kernel.execute import ExecutionContext
from afritech.epoch.epoch_snapshot import EpochSnapshot

from afritech.distributed.zt_node import ZeroTrustNode
from afritech.distributed.verifier import ProofVerifier
from afritech.distributed.proof import validate_proof_structure


class ZeroTrustRuntime:
    """
    Zero-Trust Distributed Runtime.

    Responsibilities:
    - Execute functions across zero-trust nodes
    - Collect cryptographic proofs
    - Filter invalid/malformed responses
    - Enforce consensus via ProofVerifier
    """

    def __init__(self, node_ids: List[str]) -> None:
        if not node_ids:
            raise ValueError("ZeroTrustRuntime requires at least one node")

        # ✅ Initialize nodes
        self.nodes: List[ZeroTrustNode] = [
            ZeroTrustNode(node_id) for node_id in node_ids
        ]

        # ✅ Build public key registry
        self.public_keys: Dict[str, Any] = {
            node.node_id: node.identity.public_key
            for node in self.nodes
        }

        # ✅ Proof verifier (zero-trust)
        self.verifier: ProofVerifier = ProofVerifier(self.public_keys)

    # -----------------------------------------------------
    # Execution (primary entrypoint)
    # -----------------------------------------------------

    def execute(
        self,
        fn: Callable[[ExecutionContext], Any],
        epoch_snapshot: EpochSnapshot,
    ) -> Dict[str, Any]:
        """
        Execute function across all zero-trust nodes.

        Flow:
        - Each node executes independently
        - Each node produces a signed proof
        - Invalid proofs filtered
        - Consensus enforced on valid proofs only
        """

        proofs: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []

        # ✅ Collect proofs
        for node in self.nodes:
            try:
                proof = node.execute(fn, epoch_snapshot)

                # ✅ Separate rejected responses
                if proof.get("status") == "rejected":
                    rejected.append(proof)
                    continue

                # ✅ Validate basic structure before expensive verification
                if not validate_proof_structure(proof):
                    rejected.append({
                        "node": node.node_id,
                        "status": "rejected",
                        "error": "Invalid proof structure"
                    })
                    continue

                proofs.append(proof)

            except Exception as e:
                rejected.append({
                    "node": node.node_id,
                    "status": "rejected",
                    "error": str(e),
                })

        # ✅ Ensure at least one valid proof
        if not proofs:
            raise RuntimeError("All nodes failed or produced invalid proofs")

        # ✅ Perform zero-trust consensus
        consensus_result = self.verifier.consensus(proofs)

        # ✅ Return enriched result
        return {
            "consensus": consensus_result,
            "valid_proofs": len(proofs),
            "rejected": rejected,
            "total_nodes": len(self.nodes),
        }

    # -----------------------------------------------------
    # Batch execution (advanced)
    # -----------------------------------------------------

    def execute_batch(
        self,
        functions: List[Callable[[ExecutionContext], Any]],
        epoch_snapshot: EpochSnapshot,
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple functions under zero-trust consensus.
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
        new_node = ZeroTrustNode(node_id)
        self.nodes.append(new_node)

        # ✅ Update public keys
        self.public_keys[node_id] = new_node.identity.public_key

        # ✅ Rebuild verifier
        self.verifier = ProofVerifier(self.public_keys)

    def remove_node(self, node_id: str) -> None:
        self.nodes = [n for n in self.nodes if n.get_node_id() != node_id]

        if not self.nodes:
            raise RuntimeError("Cannot remove all nodes")

        # ✅ rebuild public keys
        self.public_keys = {
            node.node_id: node.identity.public_key
            for node in self.nodes
        }

        # ✅ rebuild verifier
        self.verifier = ProofVerifier(self.public_keys)

    # -----------------------------------------------------
    # Debug / inspection
    # -----------------------------------------------------

    def get_public_keys(self) -> Dict[str, Any]:
        return self.public_keys

    def reset(self) -> None:
        """
        Reset all nodes.
        """

        for node in self.nodes:
            node.reset()
