from __future__ import annotations

import json
import os
from typing import List

DISCOVERY_FILE = "known_peers.json"


def load_peers() -> List[str]:
    if not os.path.exists(DISCOVERY_FILE):
        return []
    try:
        with open(DISCOVERY_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return [peer for peer in data if isinstance(peer, str)] if isinstance(data, list) else []
    except Exception:
        return []


def save_peer(uri: str) -> None:
    if not isinstance(uri, str) or not uri.strip():
        raise ValueError("Invalid peer URI")
    peers = load_peers()
    if uri not in peers:
        peers.append(uri)
        _write_peers(peers)


def remove_peer(uri: str) -> None:
    peers = load_peers()
    if uri in peers:
        peers.remove(uri)
        _write_peers(peers)


def clear_peers() -> None:
    _write_peers([])


def _write_peers(peers: List[str]) -> None:
    temp_file = f"{DISCOVERY_FILE}.tmp"
    try:
        with open(temp_file, "w", encoding="utf-8") as handle:
            json.dump([p for p in peers if isinstance(p, str)], handle, indent=2)
        os.replace(temp_file, DISCOVERY_FILE)
    except Exception:
        pass


from afritech.network.discovery.dht_node import DHTNode, PeerInfo

__all__ = [
    "DHTNode",
    "PeerInfo",
    "load_peers",
    "save_peer",
    "remove_peer",
    "clear_peers",
]
