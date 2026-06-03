from __future__ import annotations

import json
import os
from typing import List


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DISCOVERY_FILE = "known_peers.json"


# ---------------------------------------------------------
# Load peers
# ---------------------------------------------------------

def load_peers() -> List[str]:
    """
    Load known peer URIs from disk.

    Returns:
        List[str]: list of peer URIs
    """

    if not os.path.exists(DISCOVERY_FILE):
        return []

    try:
        with open(DISCOVERY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        # ✅ Validate data
        if not isinstance(data, list):
            return []

        # ✅ Ensure all entries are strings
        return [p for p in data if isinstance(p, str)]

    except Exception:
        # ✅ Fail-safe (never crash system)
        return []


# ---------------------------------------------------------
# Save peer
# ---------------------------------------------------------

def save_peer(uri: str) -> None:
    """
    Save a peer URI to the discovery file.
    """

    if not isinstance(uri, str) or not uri.strip():
        raise ValueError("Invalid peer URI")

    peers = load_peers()

    if uri not in peers:
        peers.append(uri)
        _write_peers(peers)


# ---------------------------------------------------------
# Remove peer
# ---------------------------------------------------------

def remove_peer(uri: str) -> None:
    """
    Remove a peer from the discovery list.
    """

    peers = load_peers()

    if uri in peers:
        peers.remove(uri)
        _write_peers(peers)


# ---------------------------------------------------------
# Clear all peers
# ---------------------------------------------------------

def clear_peers() -> None:
    """
    Remove all stored peers.
    """

    _write_peers([])


# ---------------------------------------------------------
# Internal write (atomic)
# ---------------------------------------------------------

def _write_peers(peers: List[str]) -> None:
    """
    Atomically write peers to disk.

    Prevents:
    - corrupted files
    - partial writes
    """

    temp_file = f"{DISCOVERY_FILE}.tmp"

    try:
        # ✅ Ensure only valid strings
        cleaned = [p for p in peers if isinstance(p, str)]

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2)

        # ✅ Atomic replace
        os.replace(temp_file, DISCOVERY_FILE)

    except Exception:
        # ✅ Silent fail (do not break system)
        pass