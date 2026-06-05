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
    GA-Elite Autonomous Sovereign P2P Node
    """

    # =====================================================
    # ✅ INIT
    # =====================================================

    def __init__(self, node_id: str) -> None:
        if not isinstance(node_id, str):
            raise TypeError("node_id must be a string")

        self._node_id = node_id
        self._zt_node = ZeroTrustNode(node_id)
        self._gossip = GossipEngine(node_id)

        self._proofs: List[Dict[str, Any]] = []

        # ✅ FUNCTION REGISTRY (CRITICAL FIX)
        self._registry: Dict[str, Callable] = {}

    # =====================================================
    # ✅ FUNCTION REGISTRATION
    # =====================================================

    def register_function(self, fn_id: str, fn: Callable) -> None:
        if not isinstance(fn_id, str) or not callable(fn):
            raise TypeError("Invalid function registration")

        self._registry[fn_id] = fn

    # =====================================================
    # ✅ PEER MANAGEMENT
    # =====================================================

    def connect(self, peer: NodeInterface) -> None:
        if peer is None:
            return

        if peer.get_node_id() == self._node_id:
            return

        self._gossip.add_peer(peer)

    # =====================================================
    # ✅ ENTRYPOINT
    # =====================================================

    def receive_message(self, message: GossipMessage) -> None:
        self._receive_internal(message)

    # =====================================================
    # ✅ INTERNAL RECEIVE
    # =====================================================

    def _receive_internal(self, message: GossipMessage) -> None:
        try:
            if not validate_message_structure(message):
                return

            payload_root = message.payload
            msg_type = payload_root.type
            payload = payload_root.payload

            if msg_type == "EXECUTE":
                self._handle_execute(payload)

            elif msg_type == "PROOF":
                self._handle_proof(payload)

            # ✅ Gossip propagation (loop-safe in engine)
            self._gossip.broadcast(message)

        except Exception:
            return

    # =====================================================
    # ✅ EXECUTION HANDLER (FIXED)
    # =====================================================

    def _handle_execute(self, payload: Dict[str, Any]) -> None:

        fn_id = payload.get("fn_id")
        args = payload.get("args", {})
        epoch_snapshot = payload.get("epoch")

        if not isinstance(fn_id, str):
            return

        if not isinstance(epoch_snapshot, EpochSnapshot):
            return

        fn = self._registry.get(fn_id)

        if not callable(fn):
            return

        try:
            proof = self._zt_node.execute(
                lambda ctx: fn(ctx, **args),
                epoch_snapshot,
                fn_id=fn_id,
            )

            if isinstance(proof, dict):
                self._proofs.append(proof)

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

        if isinstance(proof, dict):
            self._proofs.append(proof)

    # =====================================================
    # ✅ EXECUTION ENTRYPOINT (FIXED)
    # =====================================================

    def execute(
        self,
        fn_id: str,
        epoch_snapshot: EpochSnapshot,
        args: Dict[str, Any] | None = None,
    ) -> GossipMessage:

        if not isinstance(fn_id, str):
            raise TypeError("fn_id must be string")

        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise TypeError("Invalid EpochSnapshot")

        if args is None:
            args = {}

        message = build_message(
            "EXECUTE",
            {
                "fn_id": fn_id,
                "args": args,
                "epoch": epoch_snapshot,
            },
            self._node_id,
        )

        self._receive_internal(message)

        return message

    # =====================================================
    # ✅ STATE
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
        self._zt_node.reset()
        self._gossip.reset()
        self._proofs.clear()
        self._registry.clear()
