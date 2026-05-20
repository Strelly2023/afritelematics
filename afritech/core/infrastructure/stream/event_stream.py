# ecosystems/core/infrastructure/stream/event_stream.py

from typing import Callable, Any


class EventStream:
    """
    Lightweight in-memory event stream.

    Responsibilities:
    - Fan-out event distribution
    - Subscriber management
    - Real-time propagation layer

    Guarantees:
    - No persistence (pure distribution layer)
    - No ordering assumptions beyond publisher
    - Replay-agnostic
    """

    def __init__(self):
        # list of subscriber callbacks
        self.subscribers: list[Callable[[Any], None]] = []

    # --------------------------------------------------
    # SUBSCRIBE
    # --------------------------------------------------
    def subscribe(self, callback: Callable[[Any], None]):
        """
        Register a subscriber.

        Subscriber signature:
            callback(event_dict)
        """

        if callback not in self.subscribers:
            self.subscribers.append(callback)

    # --------------------------------------------------
    # UNSUBSCRIBE
    # --------------------------------------------------
    def unsubscribe(self, callback: Callable[[Any], None]):
        """
        Remove a subscriber.
        """

        if callback in self.subscribers:
            self.subscribers.remove(callback)

    # --------------------------------------------------
    # PUBLISH EVENT
    # --------------------------------------------------
    def publish(self, message: dict):
        """
        Broadcast event to all subscribers.

        This is a BEST-EFFORT fan-out:
        - no retries
        - no persistence
        - no ordering guarantees
        """

        for subscriber in list(self.subscribers):
            try:
                subscriber(message)
            except Exception as e:
                # Isolation guarantee:
                # one bad subscriber must NOT break stream
                print(f"[EventStream] subscriber error: {e}")

    # --------------------------------------------------
    # BROADCAST (ALIAS)
    # --------------------------------------------------
    def broadcast(self, message: dict):
        """
        Alias for publish (semantic clarity for realtime systems)
        """
        self.publish(message)

    # --------------------------------------------------
    # CLEAR ALL SUBSCRIBERS
    # --------------------------------------------------
    def clear(self):
        """
        Remove all subscribers.
        """

        self.subscribers.clear()

    # --------------------------------------------------
    # DEBUG HELPERS
    # --------------------------------------------------
    def size(self) -> int:
        """
        Number of active subscribers.
        """
        return len(self.subscribers)

    def is_empty(self) -> bool:
        """
        True if no subscribers.
        """
        return len(self.subscribers) == 0

    # --------------------------------------------------
    # SNAPSHOT (DIAGNOSTICS ONLY)
    # --------------------------------------------------
    def snapshot(self):
        """
        Non-functional introspection helper.
        """

        return {
            "subscriber_count": len(self.subscribers),
            "subscribers": [
                repr(s) for s in self.subscribers
            ],
        }