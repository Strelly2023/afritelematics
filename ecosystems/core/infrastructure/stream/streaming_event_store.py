# ecosystems/core/infrastructure/stream/streaming_event_store.py

from ecosystems.core.infrastructure.persistence.event_store import EventStore


class StreamingEventStore(EventStore):
    """
    Event store with real-time streaming support.

    Responsibilities:
    - Persist events first (source of truth)
    - Emit trace events
    - Publish real-time stream updates

    Guarantees:
    - Persistence before publication
    - Replay-safe behavior
    - Deterministic append ordering
    - Non-invasive observability
    """

    def __init__(self, stream, tracer=None):

        super().__init__()

        self.stream = stream
        self.tracer = tracer

    # --------------------------------------------------
    # APPEND EVENT
    # --------------------------------------------------
    def append(self, stream_id, expected_version, event):
        """
        Persist + trace + publish.

        Ordering is CRITICAL:

        1. Persist (truth)
        2. Trace (observability)
        3. Publish (real-time distribution)
        """

        # --------------------------------------------------
        # 1. PERSIST FIRST (SOURCE OF TRUTH)
        # --------------------------------------------------
        super().append(
            stream_id=stream_id,
            expected_version=expected_version,
            event=event,
        )

        # --------------------------------------------------
        # 2. TRACE EVENT
        # --------------------------------------------------
        if self.tracer:
            self.tracer.trace(stream_id, event)

        # --------------------------------------------------
        # 3. PUBLISH EVENT
        # --------------------------------------------------
        self.stream.publish(
            {
                "stream_id": stream_id,
                "version": expected_version + 1,
                "event": event.to_dict(),
            }
        )

    # --------------------------------------------------
    # APPEND MULTIPLE EVENTS
    # --------------------------------------------------
    def append_many(
        self,
        stream_id,
        expected_version,
        events,
    ):
        """
        Sequential append preserving ordering.

        Useful for:
        - timeout cycles
        - retries
        - batch transitions
        """

        current_version = expected_version

        for event in events:

            self.append(
                stream_id=stream_id,
                expected_version=current_version,
                event=event,
            )

            current_version += 1

    # --------------------------------------------------
    # REPLAY STREAM
    # --------------------------------------------------
    def replay(self, stream_id):
        """
        Convenience helper for replay access.
        """

        return self.load(stream_id)

    # --------------------------------------------------
    # STREAM EXISTS
    # --------------------------------------------------
    def exists(self, stream_id):

        return stream_id in self.streams

    # --------------------------------------------------
    # STREAM VERSION
    # --------------------------------------------------
    def get_version(self, stream_id):

        return len(self.streams.get(stream_id, []))

    # --------------------------------------------------
    # TOTAL EVENTS
    # --------------------------------------------------
    def total_events(self):

        return sum(
            len(events)
            for events in self.streams.values()
        )

    # --------------------------------------------------
    # TOTAL STREAMS
    # --------------------------------------------------
    def total_streams(self):

        return len(self.streams)

    # --------------------------------------------------
    # CLEAR STORE
    # --------------------------------------------------
    def clear(self):

        super().clear()

    # --------------------------------------------------
    # SNAPSHOT (DEBUGGING / TESTING)
    # --------------------------------------------------
    def snapshot(self):
        """
        Immutable diagnostic snapshot.
        """

        return {
            stream_id: [
                event.to_dict()
                for event in events
            ]
            for stream_id, events
            in self.streams.items()
        }