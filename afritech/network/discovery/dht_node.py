from __future__ import annotations

from typing import List

from afritech.network.discovery.kbucket import PeerInfo
from afritech.network.discovery.lookup import PeerLookup
from afritech.network.discovery.routing_table import RoutingTable


class DHTNode:
    def __init__(self, node_id: str, uri: str, bucket_size: int = 20) -> None:
        if not isinstance(node_id, str) or not node_id:
            raise ValueError("node_id must be non-empty")
        if not isinstance(uri, str):
            raise TypeError("uri must be a string")

        self.node_id = node_id
        self.uri = uri
        self.routing_table = RoutingTable(node_id, bucket_size=bucket_size)
        self.lookup = PeerLookup(self.routing_table)

    def join(self, bootstrap_peers: List[PeerInfo]) -> None:
        for peer in bootstrap_peers:
            self.store_peer(peer.node_id, peer.uri)

    def store_peer(self, node_id: str, uri: str) -> None:
        self.routing_table.add_peer(node_id, uri)

    def remove_peer(self, node_id: str) -> None:
        self.routing_table.remove_peer(node_id)

    def find_node(self, target_id: str, limit: int = 20) -> List[PeerInfo]:
        return self.lookup.closest(target_id, limit)

    def peers(self) -> List[PeerInfo]:
        return self.routing_table.all_peers()


__all__ = ["DHTNode", "PeerInfo"]
