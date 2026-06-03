from __future__ import annotations

from typing import Protocol, List, Any
from dataclasses import dataclass


# ============================================================
# ✅ Message Model (Deterministic)
# ============================================================

@dataclass(frozen=True)
class GossipMessage:
    """
    Deterministic gossip message.

    Must be:
    - serializable
    - replay-safe
    """

    message_id: str
    sender_id: str
    payload: Any
    timestamp: int


# ============================================================
# ✅ Node Interface
# ============================================================

class NodeInterface(Protocol):
    """
    Contract for P2P nodes.

    MUST NOT import gossip implementation.
    """

    def get_node_id(self) -> str:
        ...

    def receive_message(self, message: GossipMessage) -> None:
        ...


# ============================================================
# ✅ Gossip Interface
# ============================================================

class GossipInterface(Protocol):
    """
    Contract for gossip layer.

    MUST NOT import node implementation.
    """

    def broadcast(self, message: GossipMessage) -> None:
        ...

    def add_peer(self, peer: NodeInterface) -> None:
        ...

    def get_peers(self) -> List[NodeInterface]:
        ...


# ============================================================
# ✅ Export
# ============================================================

__all__ = [
    "GossipMessage",
    "NodeInterface",
    "GossipInterface",
]