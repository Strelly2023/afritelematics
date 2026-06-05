from __future__ import annotations

import time
from typing import Dict, List


class RateLimiter:
    """
    GA-Elite Rate Limiter (Sliding Window)

    Responsibilities:
    - Prevent abuse / DoS
    - Enforce per-peer request limits
    - Maintain bounded memory
    - Deterministic behavior

    Model:
    - Each peer has a request timestamp history
    - Old requests are cleaned automatically
    - Requests beyond limit are rejected
    """

    # =====================================================
    # ✅ INIT
    # =====================================================

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
    ) -> None:

        if not isinstance(max_requests, int) or max_requests <= 0:
            raise ValueError("max_requests must be positive int")

        if not isinstance(window_seconds, int) or window_seconds <= 0:
            raise ValueError("window_seconds must be positive int")

        self.max_requests = max_requests
        self.window = window_seconds

        # ✅ peer_id -> list[timestamps]
        self._requests: Dict[str, List[float]] = {}

    # =====================================================
    # ✅ MAIN CHECK
    # =====================================================

    def allow(self, peer_id: str) -> bool:
        """
        Determine whether a peer is allowed.

        Returns:
        - True → allowed
        - False → rate limit exceeded
        """

        if not isinstance(peer_id, str):
            return False

        now = time.time()

        history = self._requests.get(peer_id)

        if history is None:
            history = []
            self._requests[peer_id] = history

        # ✅ cleanup expired entries
        self._cleanup_peer(history, now)

        # ✅ enforce limit
        if len(history) >= self.max_requests:
            return False

        # ✅ record request
        history.append(now)

        return True

    # =====================================================
    # ✅ CLEANUP (PER PEER)
    # =====================================================

    def _cleanup_peer(self, history: List[float], now: float) -> None:
        """
        Remove timestamps outside the sliding window.
        """

        cutoff = now - self.window

        # ✅ in-place filtering (memory efficient)
        i = 0
        while i < len(history):
            if history[i] >= cutoff:
                break
            i += 1

        if i > 0:
            del history[:i]

    # =====================================================
    # ✅ GLOBAL CLEANUP (OPTIONAL)
    # =====================================================

    def cleanup(self) -> None:
        """
        Remove inactive peers completely.

        Prevents long-term memory growth.
        """

        now = time.time()
        cutoff = now - self.window

        dead_peers = []

        for peer_id, history in self._requests.items():
            self._cleanup_peer(history, now)

            if not history:
                dead_peers.append(peer_id)

        for peer_id in dead_peers:
            del self._requests[peer_id]

    # =====================================================
    # ✅ RESET
    # =====================================================

    def reset(self) -> None:
        """
        Clear all rate limiting state.
        Useful for testing or restart.
        """
        self._requests.clear()

    # =====================================================
    # ✅ INTROSPECTION (DEBUG / METRICS)
    # =====================================================

    def get_peer_request_count(self, peer_id: str) -> int:
        """
        Get request count for a peer.
        """

        history = self._requests.get(peer_id)
        if history is None:
            return 0

        now = time.time()
        self._cleanup_peer(history, now)

        return len(history)

    def get_total_peers(self) -> int:
        """
        Number of tracked peers.
        """
        return len(self._requests)
