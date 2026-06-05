from __future__ import annotations

import time
from typing import List, Dict, TYPE_CHECKING

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
    🔥 GA-Elite Gossip Propagation Engine

    Guarantees:
    - loop prevention
    - bounded memory (seen cache)
    - TTL propagation control
    - deterministic behavior
    """

    # =====================================================
    # ✅ INIT
    # =====================================================

    def __init__(self, node_id: str) -> None:
        if not isinstance(node_id, str):
            raise TypeError("node_id must be a string")

        self.node_id = node_id

        self._peers: List[NodeInterface] = []

        # ✅ message_id → timestamp
        self._seen_messages: Dict[str, float] = {}

        # ✅ cache TTL (seconds)
        self._seen_ttl: float = 60.0

    # =====================================================
    # ✅ PEER MANAGEMENT
    # =====================================================

    def add_peer(self, peer: NodeInterface) -> None:
        if peer is None:
            return

        try:
            peer_id = peer.get_node_id()
        except Exception:
            return

        if peer_id == self.node_id:
            return

        if peer not in self._peers:
            self._peers.append(peer)

    def get_peers(self) -> List[NodeInterface]:
        return list(self._peers)

    # =====================================================
    # ✅ BROADCAST (CORE)
    # =====================================================

    def broadcast(self, message: GossipMessage) -> None:
        try:
            # ✅ Step 1: Validate structure
            if not validate_message_structure(message):
                return

            # ✅ Step 2: Local handling + dedup
            if not self._handle_message(message):
                return

            # ✅ Step 3: TTL decrement
            forwarded = decrement_ttl(message)

            if is_expired(forwarded):
                return

            # ✅ Step 4: Propagate
            for peer in self._peers:
                try:
                    peer.receive_message(forwarded)
                except Exception:
                    continue

        except Exception:
            return  # fail-safe

    # =====================================================
    # ✅ INTERNAL MESSAGE HANDLING
    # =====================================================

    def _handle_message(self, message: GossipMessage) -> bool:
        msg_id = getattr(message, "message_id", None)

        if not isinstance(msg_id, str):
            return False

        now = time.time()

        # ✅ cleanup BEFORE check
        self._cleanup_seen(now)

        # ✅ duplicate filtering
        if msg_id in self._seen_messages:
            return False

        # ✅ TTL enforcement
        if is_expired(message):
            return False

        # ✅ mark as seen
        self._seen_messages[msg_id] = now

        return True

    # =====================================================
    # ✅ CLEANUP (CRITICAL FIX)
    # =====================================================

    def _cleanup_seen(self, now: float) -> None:
        """
        Prevent unbounded memory growth.
        """

        expired_keys = [
            msg_id for msg_id, ts in self._seen_messages.items()
            if now - ts > self._seen_ttl
        ]

        for key in expired_keys:
            del self._seen_messages[key]

    # =====================================================
    # ✅ INBOUND ENTRYPOINT
    # =====================================================

    def receive(self, message: GossipMessage) -> None:
        self.broadcast(message)

    # =====================================================
    # ✅ UTILITIES
    # =====================================================

    def get_peer_ids(self) -> List[str]:
        peer_ids: List[str] = []

        for peer in self._peers:
            try:
                peer_ids.append(peer.get_node_id())
            except Exception:
                peer_ids.append("unknown")

        return peer_ids

    def reset(self) -> None:
        self._seen_messages.clear()
