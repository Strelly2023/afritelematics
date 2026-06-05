from __future__ import annotations

from typing import List

from afritech.network.discovery.distance import normalize_node_id, sort_by_distance, xor_distance
from afritech.network.discovery.kbucket import KBucket, PeerInfo


class RoutingTable:
    def __init__(self, node_id: str, bucket_size: int = 20, id_bits: int = 256) -> None:
        self.node_id = node_id
        self.id_bits = id_bits
        self._buckets = [KBucket(bucket_size) for _ in range(id_bits)]

    def add_peer(self, node_id: str, uri: str) -> None:
        if node_id == self.node_id:
            return
        self._buckets[self._bucket_index(node_id)].add_or_touch(node_id, uri)

    def remove_peer(self, node_id: str) -> None:
        self._buckets[self._bucket_index(node_id)].remove(node_id)

    def all_peers(self) -> List[PeerInfo]:
        peers: List[PeerInfo] = []
        for bucket in self._buckets:
            peers.extend(bucket.peers())
        return peers

    def closest(self, target_id: str, limit: int = 20) -> List[PeerInfo]:
        return sort_by_distance(target_id, self.all_peers(), lambda peer: peer.node_id)[:limit]

    def _bucket_index(self, peer_id: str) -> int:
        distance = xor_distance(self.node_id, peer_id)
        if distance == 0:
            return 0
        return min(distance.bit_length() - 1, self.id_bits - 1)

    def local_int_id(self) -> int:
        return normalize_node_id(self.node_id)
