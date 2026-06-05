from __future__ import annotations

from dataclasses import dataclass
import time
from typing import List


@dataclass(frozen=True)
class PeerInfo:
    node_id: str
    uri: str
    last_seen: float


class KBucket:
    def __init__(self, k: int = 20) -> None:
        if not isinstance(k, int) or k <= 0:
            raise ValueError("k must be positive")
        self.k = k
        self._peers: List[PeerInfo] = []

    def add_or_touch(self, node_id: str, uri: str) -> None:
        now = time.time()
        existing = [peer for peer in self._peers if peer.node_id == node_id]
        self._peers = [peer for peer in self._peers if peer.node_id != node_id]

        peer = PeerInfo(
            node_id=node_id,
            uri=uri if uri else (existing[0].uri if existing else ""),
            last_seen=now,
        )
        self._peers.append(peer)

        if len(self._peers) > self.k:
            self._peers = self._peers[-self.k:]

    def remove(self, node_id: str) -> None:
        self._peers = [peer for peer in self._peers if peer.node_id != node_id]

    def peers(self) -> List[PeerInfo]:
        return list(self._peers)
