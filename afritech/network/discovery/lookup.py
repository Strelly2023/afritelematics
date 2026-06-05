from __future__ import annotations

from typing import Iterable, List

from afritech.network.discovery.distance import sort_by_distance
from afritech.network.discovery.kbucket import PeerInfo
from afritech.network.discovery.routing_table import RoutingTable


class PeerLookup:
    def __init__(self, routing_table: RoutingTable, alpha: int = 3) -> None:
        if not isinstance(alpha, int) or alpha <= 0:
            raise ValueError("alpha must be positive")
        self.routing_table = routing_table
        self.alpha = alpha

    def closest(self, target_id: str, limit: int = 20) -> List[PeerInfo]:
        return self.routing_table.closest(target_id, limit)

    def merge_candidates(
        self,
        target_id: str,
        candidates: Iterable[PeerInfo],
        limit: int = 20,
    ) -> List[PeerInfo]:
        by_id = {peer.node_id: peer for peer in self.routing_table.all_peers()}
        for peer in candidates:
            by_id[peer.node_id] = peer
        return sort_by_distance(target_id, by_id.values(), lambda peer: peer.node_id)[:limit]
