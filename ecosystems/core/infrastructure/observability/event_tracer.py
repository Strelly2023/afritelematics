from datetime import datetime, UTC


class EventTracer:
    """
    Lightweight in-memory event tracing system.

    Responsibilities:
    - trace event flow
    - provide execution visibility
    - support debugging + diagnostics
    - preserve replay observability

    Characteristics:
    - append-only
    - deterministic
    - side-effect isolated
    - test-friendly
    """

    def __init__(self):

        # --------------------------------------------------
        # Ordered trace log entries
        # --------------------------------------------------
        self.logs = []

    # ==================================================
    # TRACE EVENT
    # ==================================================
    def trace(self, stream_id, event):
        """
        Record event trace entry.
        """

        entry = {
            "stream_id": stream_id,
            "event_id": event.event_id,
            "event_type": event.type,
            "timestamp": event.timestamp,
            "payload": dict(event.payload),

            # Internal trace timestamp (FIXED: timezone-aware)
            "traced_at": datetime.now(UTC).isoformat(),
        }

        self.logs.append(entry)

        # --------------------------------------------------
        # Console visibility
        # --------------------------------------------------
        print(
            f"[TRACE] "
            f"stream={stream_id} "
            f"event={event.type} "
            f"id={event.event_id}"
        )

    # ==================================================
    # READ OPERATIONS
    # ==================================================

    # --------------------------------------------------
    # ALL LOGS
    # --------------------------------------------------
    def get_logs(self):
        """
        Immutable copy of logs.
        """

        return list(self.logs)

    # --------------------------------------------------
    # FILTER BY STREAM
    # --------------------------------------------------
    def get_stream_logs(self, stream_id):
        """
        Get logs for one stream.
        """

        return [
            log
            for log in self.logs
            if log["stream_id"] == stream_id
        ]

    # --------------------------------------------------
    # FILTER BY EVENT TYPE
    # --------------------------------------------------
    def get_event_logs(self, event_type):
        """
        Get logs by event type.
        """

        return [
            log
            for log in self.logs
            if log["event_type"] == event_type
        ]

    # --------------------------------------------------
    # FIND BY EVENT ID
    # --------------------------------------------------
    def find_event(self, event_id):
        """
        Find single traced event.
        """

        for log in self.logs:
            if log["event_id"] == event_id:
                return log

        return None

    # ==================================================
    # SUMMARY OPERATIONS
    # ==================================================

    # --------------------------------------------------
    # TRACE COUNT
    # --------------------------------------------------
    def count(self):
        """
        Total traced events.
        """

        return len(self.logs)

    # --------------------------------------------------
    # STREAM COUNT
    # --------------------------------------------------
    def stream_count(self):
        """
        Total unique streams traced.
        """

        return len({
            log["stream_id"]
            for log in self.logs
        })

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------
    def summary(self):
        """
        Aggregate trace summary.
        """

        event_types = {}

        for log in self.logs:
            et = log["event_type"]
            event_types[et] = event_types.get(et, 0) + 1

        return {
            "total_logs": self.count(),
            "streams": self.stream_count(),
            "event_types": event_types,
        }

    # ==================================================
    # CLEAR OPERATIONS
    # ==================================================

    # --------------------------------------------------
    # CLEAR ALL LOGS
    # --------------------------------------------------
    def clear(self):
        """
        Clear all trace logs.
        """

        self.logs.clear()

    # --------------------------------------------------
    # CLEAR SINGLE STREAM
    # --------------------------------------------------
    def clear_stream(self, stream_id):
        """
        Remove logs for one stream only.
        """

        self.logs = [
            log
            for log in self.logs
            if log["stream_id"] != stream_id
        ]

    # ==================================================
    # EXPORT / SERIALIZATION
    # ==================================================

    # --------------------------------------------------
    # SERIALIZE
    # --------------------------------------------------
    def to_dict(self):
        """
        Export trace state.
        """

        return {
            "logs": self.get_logs(),
            "summary": self.summary(),
        }

    # ==================================================
    # DEBUG REPRESENTATION
    # ==================================================
    def __repr__(self):

        return (
            "EventTracer("
            f"logs={self.count()}, "
            f"streams={self.stream_count()}"
            ")"
        )