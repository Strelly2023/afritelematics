"""
AfriTech Queue Runtime

PURPOSE:
--------
Provides the core queue abstraction for async execution.

Responsibilities:
- Store events in FIFO queues
- Support partitioned queues (locality-aware)
- Enable safe enqueue/dequeue
- Track queue metrics (for adaptive layer)
- Support backpressure control
- Remain deterministic-safe (NO mutation)

FUTURE:
-------
- Replaceable with Kafka / Redis / NATS
- Distributed queue compatibility
"""

from collections import defaultdict, deque
import threading


class QueueRuntime:
    """
    In-memory queue engine (thread-safe).

    Design goals:
    - deterministic FIFO order
    - non-blocking operations
    - partition-aware
    """

    def __init__(self):
        self.queues = defaultdict(deque)
        self.locks = defaultdict(threading.Lock)

    # ============================================================
    # ✅ ENQUEUE
    # ============================================================

    def enqueue(self, queue_name: str, event: dict):
        """
        Add event to queue.

        Guarantees:
        - FIFO order preserved
        - does NOT mutate event
        """

        if not isinstance(queue_name, str):
            raise TypeError("Queue name must be a string")

        if not isinstance(event, dict):
            raise TypeError("Event must be a dictionary")

        with self.locks[queue_name]:
            self.queues[queue_name].append(event)

    # ============================================================
    # ✅ DEQUEUE
    # ============================================================

    def dequeue(self, queue_name: str):
        """
        Remove event from queue (FIFO).

        Returns:
        - event dict
        - None if empty
        """

        if queue_name not in self.queues:
            return None

        with self.locks[queue_name]:
            if self.queues[queue_name]:
                return self.queues[queue_name].popleft()

        return None

    # ============================================================
    # ✅ PEEK
    # ============================================================

    def peek(self, queue_name: str):
        """
        Look at next event WITHOUT removing it.
        """

        with self.locks[queue_name]:
            if self.queues[queue_name]:
                return self.queues[queue_name][0]

        return None

    # ============================================================
    # ✅ QUEUE LENGTH
    # ============================================================

    def get_queue_length(self, queue_name: str) -> int:
        """
        Return queue size.
        """

        return len(self.queues[queue_name])

    # ============================================================
    # ✅ ALL QUEUES SNAPSHOT
    # ============================================================

    def snapshot(self):
        """
        Create a snapshot of queue sizes (safe for telemetry).
        """

        return {
            queue_name: len(queue)
            for queue_name, queue in self.queues.items()
        }

    # ============================================================
    # ✅ BULK DEQUEUE (BATCH SUPPORT)
    # ============================================================

    def dequeue_batch(self, queue_name: str, max_items: int):
        """
        Remove up to max_items from queue.

        Guarantees:
        - preserves order
        - safe batching
        """

        batch = []

        with self.locks[queue_name]:
            for _ in range(min(max_items, len(self.queues[queue_name]))):
                batch.append(self.queues[queue_name].popleft())

        return batch

    # ============================================================
    # ✅ CLEAR QUEUE
    # ============================================================

    def clear_queue(self, queue_name: str):
        """
        Completely empties a queue.
        """

        with self.locks[queue_name]:
            self.queues[queue_name].clear()

    # ============================================================
    # ✅ EXISTENCE CHECK
    # ============================================================

    def has_queue(self, queue_name: str) -> bool:
        return queue_name in self.queues

    # ============================================================
    # ✅ BACKPRESSURE CHECK
    # ============================================================

    def check_backpressure(self, threshold: int = 1000):
        """
        Identify queues under pressure.

        Returns:
        dict of overloaded queues
        """

        pressure = {}

        for queue_name, queue in self.queues.items():
            size = len(queue)
            if size > threshold:
                pressure[queue_name] = size

        return pressure

    # ============================================================
    # ✅ GLOBAL SIZE
    # ============================================================

    def total_size(self) -> int:
        """
        Total events across all queues.
        """

        return sum(len(queue) for queue in self.queues.values())

    # ============================================================
    # ✅ SAFE ITERATION (READ-ONLY)
    # ============================================================

    def list_queues(self):
        """
        Return list of queue names.
        """

        return list(self.queues.keys())

    # ============================================================
    # ✅ DEBUG VIEW
    # ============================================================

    def debug_view(self):
        """
        Lightweight debug info.
        """

        return {
            "queues": self.snapshot(),
            "total_events": self.total_size(),
        }


# ============================================================
# ✅ FACTORY (FUTURE EXTENSION POINT)
# ============================================================

def create_queue_runtime(mode: str = "memory"):
    """
    Factory for queue runtime.

    Future:
    - kafka
    - redis
    - distributed queue
    """

    if mode == "memory":
        return QueueRuntime()

    raise NotImplementedError(f"Queue mode '{mode}' not supported")