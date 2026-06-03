"""
AfriTech Span

PURPOSE:
--------
Represents a unit of execution within a trace.

Responsibilities:
- track start/end time
- measure duration
- store metadata
- support nested spans (parent/child)
- enable deterministic trace structure

CRITICAL LAW:
-------------
Span MAY:
- record execution timing
- store metadata

Span may NOT:
- modify execution
- mutate event payload
- influence system behavior
"""

import time
import uuid


# ============================================================
# ✅ SPAN CLASS
# ============================================================

class Span:
    """
    Represents a single unit of work within a trace.

    Example:
        dispatcher → worker → orchestration → adapter

        Each step = one span
    """

    def __init__(self, name: str, trace_id: str = None, parent_id: str = None):
        """
        Initialize span.

        Args:
            name: logical name of the span
            trace_id: associated trace
            parent_id: parent span (for hierarchy)
        """

        if not isinstance(name, str):
            raise TypeError("Span name must be a string")

        self.span_id = str(uuid.uuid4())
        self.trace_id = trace_id
        self.parent_id = parent_id

        self.name = name

        self.start_time = time.time()
        self.end_time = None

        self.metadata = {}
        self.tags = {}

    # ========================================================
    # ✅ FINISH SPAN
    # ========================================================

    def finish(self):
        """
        Mark span as completed.
        """

        if self.end_time is None:
            self.end_time = time.time()

    # ========================================================
    # ✅ SET METADATA
    # ========================================================

    def set_metadata(self, key: str, value):
        """
        Add metadata (non-semantic information).
        """

        if not isinstance(key, str):
            raise TypeError("Metadata key must be string")

        self.metadata[key] = value

    # ========================================================
    # ✅ ADD TAG
    # ========================================================

    def add_tag(self, key: str, value):
        """
        Attach tag (used for filtering/analytics).
        """

        if not isinstance(key, str):
            raise TypeError("Tag key must be string")

        self.tags[key] = value

    # ========================================================
    # ✅ GET DURATION
    # ========================================================

    def duration(self):
        """
        Compute span duration.
        """

        if self.end_time is None:
            return None

        return self.end_time - self.start_time

    # ========================================================
    # ✅ IS FINISHED
    # ========================================================

    def is_finished(self):
        """
        Check if span is completed.
        """

        return self.end_time is not None

    # ========================================================
    # ✅ TO DICT (SERIALIZATION)
    # ============================================================

    def to_dict(self):
        """
        Convert span to dictionary for storage/export.
        """

        return {
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "start": self.start_time,
            "end": self.end_time,
            "duration": self.duration(),
            "metadata": dict(self.metadata),
            "tags": dict(self.tags),
        }

    # ========================================================
    # ✅ VALIDATION
    # ============================================================

    def validate(self):
        """
        Ensure span structure is valid.
        """

        if not isinstance(self.name, str):
            raise Exception("[SPAN ERROR] Invalid name")

        if self.end_time is not None and self.end_time < self.start_time:
            raise Exception("[SPAN ERROR] Invalid timing")

        if not isinstance(self.metadata, dict):
            raise Exception("[SPAN ERROR] Invalid metadata structure")

        if not isinstance(self.tags, dict):
            raise Exception("[SPAN ERROR] Invalid tags structure")

        return True

    # ========================================================
    # ✅ DETERMINISM CHECK
    # ============================================================

    def validate_determinism(self):
        """
        Ensure deterministic structure (not timing).
        """

        d1 = self.to_dict()
        d2 = self.to_dict()

        # Ignore time fields
        for key in ["start", "end", "duration"]:
            d1.pop(key, None)
            d2.pop(key, None)

        if d1 != d2:
            raise Exception("[SPAN ERROR] Non-deterministic structure")

        return True

    # ========================================================
    # ✅ TRACE RELATIONSHIP
    # ============================================================

    def is_root(self):
        """
        Check if span has no parent.
        """

        return self.parent_id is None

    # ========================================================
    # ✅ DEBUG VIEW
    # ============================================================

    def debug(self):
        """
        Human-readable span summary.
        """

        return {
            "name": self.name,
            "duration": self.duration(),
            "tags": self.tags,
        }