from typing import Dict, List, Optional
from ecosystems.core.domain.errors.version_conflict import VersionConflictError


class EventStore:
    """
    Event Store (in-memory, production-upgrade-ready)

    Guarantees:
    - Append-only event streams
    - Optimistic concurrency control
    - Deterministic ordering
    - Replay-safe storage
    - Supports both sync projections and async streaming

    Notes:
    - In-memory storage (can later swap to Postgres/Kafka)
    - EventBus integration enables distributed architecture
    """

    def __init__(self, event_bus=None):
        # stream_id -> [events]
        self.streams: Dict[str, List] = {}

        # Synchronous projection bus (legacy/local mode)
        self.projection_bus = None

        # Async event bus (Redis Streams / Kafka)
        self.event_bus = event_bus

    # --------------------------------------------------
    # BUS INJECTION
    # --------------------------------------------------
    def set_projection_bus(self, bus):
        """
        Attach synchronous ProjectionBus (optional).
        """
        self.projection_bus = bus

    def set_event_bus(self, bus):
        """
        Attach async EventBus (Redis Streams / Kafka).
        """
        self.event_bus = bus

    # --------------------------------------------------
    # APPEND (WITH VERSION CHECK)
    # --------------------------------------------------
    def append(self, stream_id: str, expected_version: int, event):
        """
        Append event to stream with optimistic concurrency control.

        Flow:
        1. Validate version
        2. Append event
        3. Publish event (sync + async)
        """

        stream = self.streams.get(stream_id, [])

        # ---------------------------------------------
        # CONCURRENCY CHECK (CRITICAL INVARIANT)
        # ---------------------------------------------
        current_version = len(stream)

        if current_version != expected_version:
            raise VersionConflictError(
                stream_id=stream_id,
                expected=expected_version,
                actual=current_version,
            )

        # ---------------------------------------------
        # APPEND EVENT (SOURCE OF TRUTH)
        # ---------------------------------------------
        stream.append(event)

        # Write back safely
        self.streams[stream_id] = stream

        # ---------------------------------------------
        # SYNC PROJECTION FAN-OUT (LOCAL MODE)
        # ---------------------------------------------
        if self.projection_bus:
            try:
                self.projection_bus.publish(event)
            except Exception as e:
                self._handle_error("projection_bus", event, e)

        # ---------------------------------------------
        # ASYNC EVENT STREAM (DISTRIBUTED MODE)
        # ---------------------------------------------
        if self.event_bus:
            try:
                self.event_bus.publish(event)
            except Exception as e:
                self._handle_error("event_bus", event, e)

    # --------------------------------------------------
    # LOAD STREAM
    # --------------------------------------------------
    def load(self, stream_id: str):
        """
        Load all events for a given stream.

        Returns a copy to preserve immutability.
        """
        return list(self.streams.get(stream_id, []))

    # --------------------------------------------------
    # LOAD ALL STREAMS (DEBUG / ADMIN)
    # --------------------------------------------------
    def load_all(self):
        """
        Returns full event store snapshot.
        """
        return {
            stream_id: list(events)
            for stream_id, events in self.streams.items()
        }

    # --------------------------------------------------
    # GET VERSION
    # --------------------------------------------------
    def version(self, stream_id: str) -> int:
        """
        Returns current version of a stream.
        """
        return len(self.streams.get(stream_id, []))

    # --------------------------------------------------
    # CLEAR (TESTING ONLY)
    # --------------------------------------------------
    def clear(self):
        """
        Reset store (used for tests only).
        """
        self.streams = {}

    # --------------------------------------------------
    # REPLAY SUPPORT (FULL SYSTEM REBUILD)
    # --------------------------------------------------
    def replay(self, projection_bus):
        """
        Replay all events into a projection bus.

        Useful for:
        - rebuilding projections
        - migration
        - debugging
        """
        for stream_id in self.streams:
            for event in self.streams[stream_id]:
                projection_bus.publish(event)

    # --------------------------------------------------
    # INTERNAL ERROR HANDLING
    # --------------------------------------------------
    def _handle_error(self, layer: str, event, error: Exception):
        """
        Error isolation layer (fail-soft design).
        """
        print(
            f"[EventStore ERROR] "
            f"layer={layer} "
            f"event={getattr(event, 'type', None)} "
            f"error={str(error)}"
        )
