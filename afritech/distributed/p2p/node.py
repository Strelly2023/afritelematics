from __future__ import annotations

from typing import Callable, Any, Dict, List

from afritech.distributed.p2p.message import (
    build_message,
    validate_message_structure,
)
from afritech.distributed.contracts.p2p_interface import (
    GossipMessage,
    NodeInterface,
)
from afritech.distributed.p2p.gossip import GossipEngine
from afritech.distributed.zt_node import ZeroTrustNode
from afritech.runtime.kernel.execute import ExecutionContext
from afritech.epoch.epoch_snapshot import EpochSnapshot


class P2PNode(NodeInterface):
    """
    Fully autonomous peer node (GA Elite compliant).

    Responsibilities:
    - Participate in gossip network
    - Execute distributed functions
    - Generate zero-trust proofs
    - Propagate results across mesh

    Guarantees:
    - Deterministic behavior
    - No circular dependencies with gossip
    - Contract-compliant message handling
    """

    # =====================================================
    # ✅ INIT
    # =====================================================

    def __init__(self, node_id: str) -> None:
        if not isinstance(node_id, str):
            raise TypeError("node_id must be a string")

        self._node_id: str = node_id
        self._zt_node: ZeroTrustNode = ZeroTrustNode(node_id)
        self._gossip: GossipEngine = GossipEngine(node_id)

        self._proofs: List[Dict[str, Any]] = []

    # =====================================================
    # ✅ PEER MANAGEMENT
    # =====================================================

    def connect(self, peer: NodeInterface) -> None:
        """
        Connect to another node.
        """

        if peer is None:
            return

        if peer.get_node_id() == self._node_id:
            return

        self._gossip.add_peer(peer)

    # =====================================================
    # ✅ CONTRACT ENTRYPOINT (STRICT)
    # =====================================================

    def receive_message(self, message: GossipMessage) -> None:
        """
        Entry point required by NodeInterface.
        """

        self._receive_internal(message)

    # =====================================================
    # ✅ INTERNAL RECEIVE
    # =====================================================

    def _receive_internal(self, message: GossipMessage) -> None:
        """
        Internal message processing.
        """

        try:
            if not validate_message_structure(message):
                return

            # ✅ Extract structured payload
            payload_root = message.payload
            msg_type = payload_root.get("type")
            payload = payload_root.get("payload", {})

            if msg_type == "EXECUTE":
                self._handle_execute(payload)

            elif msg_type == "PROOF":
                self._handle_proof(payload)

            # ✅ Propagation handled by gossip engine
            self._gossip.broadcast(message)

        except Exception:
            return  # fail-safe

    # =====================================================
    # ✅ EXECUTION HANDLER
    # =====================================================

    def _handle_execute(self, payload: Dict[str, Any]) -> None:
        fn = payload.get("fn")
        epoch_snapshot = payload.get("epoch")

        if not callable(fn):
            return

        if not isinstance(epoch_snapshot, EpochSnapshot):
            return

        try:
            # ✅ Execute via zero-trust node
            proof = self._zt_node.execute(fn, epoch_snapshot)

            proof_msg = build_message(
                "PROOF",
                {"proof": proof},
                self._node_id,
            )

            self._gossip.broadcast(proof_msg)

        except Exception:
            return

    # =====================================================
    # ✅ PROOF HANDLER
    # =====================================================

    def _handle_proof(self, payload: Dict[str, Any]) -> None:
        proof = payload.get("proof")

        if not isinstance(proof, dict):
            return

        self._proofs.append(proof)

    # =====================================================
    # ✅ EXECUTION ENTRYPOINT
    # =====================================================

    def execute(
        self,
        fn: Callable[[ExecutionContext], Any],
        epoch_snapshot: EpochSnapshot,
    ) -> None:
        """
        Inject execution into the P2P network.
        """

        if not callable(fn):
            raise TypeError("fn must be callable")

        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise TypeError("Invalid EpochSnapshot")

        message = build_message(
            "EXECUTE",
            {
                "fn": fn,
                "epoch": epoch_snapshot,
            },
            self._node_id,
        )

        self._gossip.broadcast(message)

    # =====================================================
    # ✅ STATE MANAGEMENT
    # =====================================================

    def get_proofs(self) -> List[Dict[str, Any]]:
        return list(self._proofs)

    def clear_proofs(self) -> None:
        self._proofs.clear()

    def get_node_id(self) -> str:
        return self._node_id

    def get_peer_ids(self) -> List[str]:
        return self._gossip.get_peer_ids()

    def reset(self) -> None:
        """
        Reset node state.
        """

        self._zt_node.reset()
        self._gossip.reset()
        self._proofs.clear()