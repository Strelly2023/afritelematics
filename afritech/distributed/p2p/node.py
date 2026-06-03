from __future__ import annotations

from typing import Callable, Any, Dict, List

from afritech.distributed.p2p.message import (
    build_message,
    validate_message_structure,
)
from afritech.distributed.p2p.gossip import GossipEngine
from afritech.distributed.zt_node import ZeroTrustNode
from afritech.runtime.kernel.execute import ExecutionContext
from afritech.epoch.epoch_snapshot import EpochSnapshot


class P2PNode:
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

    def connect(self, peer: P2PNode) -> None:
        """
        Connect to another node.

        Gossip engine only depends on interface behavior.
        """

        if not isinstance(peer, P2PNode):
            return

        self._gossip.add_peer(peer)

    # =====================================================
    # ✅ CONTRACT ENTRYPOINT (CRITICAL FIX)
    # =====================================================

    def receive_message(self, message: Dict[str, Any]) -> None:
        """
        Contract-compliant entrypoint used by gossip engine.

        This replaces `receive()` to match NodeInterface.
        """

        self._receive_internal(message)

    # =====================================================
    # ✅ INTERNAL RECEIVE
    # =====================================================

    def _receive_internal(self, message: Dict[str, Any]) -> None:
        """
        Internal message processing.

        Flow:
        - validate message
        - process based on type
        - delegate propagation to gossip engine
        """

        try:
            # ✅ Validate structure
            if not validate_message_structure(message):
                return

            msg_type = message.get("type")

            if msg_type == "EXECUTE":
                self._handle_execute(message)

            elif msg_type == "PROOF":
                self._handle_proof(message)

            # ✅ Let gossip engine manage propagation
            self._gossip.broadcast(message)

        except Exception:
            # Fail-safe: never crash node
            return

    # =====================================================
    # ✅ EXECUTION HANDLER
    # =====================================================

    def _handle_execute(self, message: Dict[str, Any]) -> None:
        payload = message.get("payload", {})

        fn = payload.get("fn")
        epoch_snapshot = payload.get("epoch")

        # ✅ Strict validation
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

            # ✅ Broadcast proof to network
            self._gossip.broadcast(proof_msg)

        except Exception:
            # Fail-safe
            return

    # =====================================================
    # ✅ PROOF HANDLER
    # =====================================================

    def _handle_proof(self, message: Dict[str, Any]) -> None:
        payload = message.get("payload", {})
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

        This is the external trigger.
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

        # ✅ Start propagation
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
