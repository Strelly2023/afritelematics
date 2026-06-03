from __future__ import annotations

from typing import List, Set, TYPE_CHECKING

from afritech.distributed.p2p.message import (
    validate_message_structure,
    decrement_ttl,
    is_expired,
)
from afritech.distributed.contracts.p2p_interface import GossipMessage

if TYPE_CHECKING:
    from afritech.distributed.contracts.p2p_interface import NodeInterface


class GossipEngine:
    """
    Gossip propagation layer (GA Elite compliant).

    Responsibilities:
    - Broadcast messages across peers
    - Prevent message loops (seen set)
    - Control propagation using TTL
    - Validate messages before forwarding

    Guarantees:
    - No circular dependencies (uses NodeInterface only)
    - Deterministic propagation behavior
    - Fail-safe execution (never crashes)
    """

    # =====================================================
    # ✅ INIT
    # =====================================================

    def __init__(self, node_id: str) -> None:
        if not isinstance(node_id, str):
            raise TypeError("node_id must be a string")

        self.node_id: str = node_id
        self._peers: List[NodeInterface] = []
        self._seen_messages: Set[str] = set()

    # =====================================================
    # ✅ PEER MANAGEMENT
    # =====================================================

    def add_peer(self, peer: NodeInterface) -> None:
        """
        Add a peer to gossip network.

        Rules:
        - No self-reference
        - No duplicates
        """

        if peer is None:
            return

        peer_id = getattr(peer, "get_node_id", lambda: None)()

        if peer_id == self.node_id:
            return

        if peer not in self._peers:
            self._peers.append(peer)

    def get_peers(self) -> List[NodeInterface]:
        """
        Return peer list (read-only copy).
        """
        return list(self._peers)

    # =====================================================
    # ✅ BROADCAST
    # =====================================================

    def broadcast(self, message: GossipMessage) -> None:
        """
        Broadcast message to all peers.

        Flow:
        - validate message
        - process locally
        - forward to peers (TTL-controlled)
        """

        try:
            # ✅ Step 1: Validate structure
            if not validate_message_structure(message):
                return

            # ✅ Step 2: Process locally
            if not self._handle_message(message):
                return

            # ✅ Step 3: Decrement TTL
            forwarded_message = decrement_ttl(message)

            # ✅ Step 4: Stop if expired
            if is_expired(forwarded_message):
                return

            # ✅ Step 5: Forward to peers
            for peer in self._peers:
                try:
                    peer.receive_message(forwarded_message)
                except Exception:
                    continue  # fail-safe

        except Exception:
            return  # global fail-safe

    # =====================================================
    # ✅ INTERNAL MESSAGE HANDLING
    # =====================================================

    def _handle_message(self, message: GossipMessage) -> bool:
        """
        Process incoming message.

        Returns:
            True → propagate further
            False → stop propagation
        """

        msg_id = message.message_id

        # ✅ Reject invalid ID
        if not isinstance(msg_id, str):
            return False

        # ✅ Prevent duplicate processing
        if msg_id in self._seen_messages:
            return False

        # ✅ Mark as seen
        self._seen_messages.add(msg_id)

        # ✅ Reject expired messages
        if is_expired(message):
            return False

        return True

    # =====================================================
    # ✅ INBOUND ENTRYPOINT
    # =====================================================

    def receive(self, message: GossipMessage) -> None:
        """
        Receive message from external peer.

        This method is optional if using NodeInterface correctly,
        but kept for compatibility/debug/testing.
        """

        self.broadcast(message)

    # =====================================================
    # ✅ UTILITIES
    # =====================================================

    def get_peer_ids(self) -> List[str]:
        """
        Return peer IDs.
        """

        peer_ids: List[str] = []

        for peer in self._peers:
            try:
                peer_ids.append(peer.get_node_id())
            except Exception:
                peer_ids.append("unknown")

        return peer_ids

    def reset(self) -> None:
        """
        Reset gossip state.
        """

        self._seen_messages.clear()
