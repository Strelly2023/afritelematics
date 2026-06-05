from __future__ import annotations

from typing import Protocol, List, Dict, Any
from dataclasses import dataclass


# ============================================================
# ✅ Payload Model (Deterministic Schema)
# ============================================================

@dataclass(frozen=True)
class MessagePayload:
    """
    Strongly-typed message payload structure.

    Guarantees:
    - deterministic shape
    - JSON-serializable
    - replay-safe
    """

    type: str
    payload: Dict[str, Any]
    ttl: int
    version: str


# ============================================================
# ✅ Gossip Message (FINAL MODEL)
# ============================================================

@dataclass(frozen=True)
class GossipMessage:
    """
    Deterministic gossip message.

    MUST be:
    - immutable
    - hashable
    - serializable
    - replay-safe
    """

    message_id: str
    sender_id: str
    payload: MessagePayload
    timestamp: int


# ============================================================
# ✅ Node Interface (STRICT CONTRACT)
# ============================================================

class NodeInterface(Protocol):
    """
    Contract for P2P nodes.

    MUST NOT depend on gossip implementation.
    MUST remain minimal and stable.
    """

    def get_node_id(self) -> str:
        ...

    def receive_message(self, message: GossipMessage) -> None:
        ...


# ============================================================
# ✅ Gossip Interface (STRICT CONTRACT)
# ============================================================

class GossipInterface(Protocol):
    """
    Contract for gossip layer.

    MUST NOT depend on node implementation.
    MUST enforce deterministic message flow.
    """

    def broadcast(self, message: GossipMessage) -> None:
        ...

    def add_peer(self, peer: NodeInterface) -> None:
        ...

    def get_peers(self) -> List[NodeInterface]:
        ...


# ============================================================
# ✅ EXPORTS
# ============================================================

__all__ = [
    "GossipMessage",
    "MessagePayload",
    "NodeInterface",
    "GossipInterface",
]