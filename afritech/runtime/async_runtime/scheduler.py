"""
AfriTech Async Scheduler

PURPOSE:
--------
Coordinates WHEN work executes across queues and workers.

Responsibilities:
- trigger worker execution cycles
- distribute execution across queues fairly
- support adaptive prioritization
- handle scheduling strategies (round-robin, priority, etc.)
- integrate backpressure awareness

CRITICAL LAW:
-------------
Scheduler MAY:
- decide execution timing
- balance load across queues
- prioritize work

Scheduler may NOT:
- mutate events
- define execution truth
- alter semantics
"""

import time


class Scheduler:
    """
    Controls WHEN and HOW workers are invoked.
    """

    def __init__(
        self,
        worker_runtime,
        queue_runtime,
        sleep_interval=0.01,
    ):
        self.worker_runtime = worker_runtime
        self.queue_runtime = queue_runtime
        self.sleep_interval = sleep_interval

    # ============================================================
    # ✅ SINGLE SCHEDULING TICK
    # ============================================================

    def tick(self, queue_names, context):
        """
        Executes one scheduling cycle across queues.
        """

        results = []

        for queue_name in queue_names:
            result = self.worker_runtime.run_once(queue_name, context)
            results.append(result)

        return results

    # ============================================================
    # ✅ CONTINUOUS RUN LOOP
    # ============================================================

    def run(self, context, max_cycles=None):
        """
        Continuous scheduling loop.

        max_cycles:
            for testing / simulation control
        """

        cycle = 0
        results = []

        while True:
            queues = self.queue_runtime.list_queues()

            tick_result = self.tick(queues, context)
            results.extend(tick_result)

            cycle += 1

            if max_cycles and cycle >= max_cycles:
                break

            time.sleep(self.sleep_interval)

        return results

    # ============================================================
    # ✅ ROUND ROBIN SCHEDULING
    # ============================================================

    def run_round_robin(self, context, max_cycles=None):
        """
        Fair rotation across queues.
        """

        cycle = 0
        results = []

        while True:
            queue_names = self.queue_runtime.list_queues()

            for queue_name in queue_names:
                result = self.worker_runtime.run_once(queue_name, context)
                results.append(result)

            cycle += 1

            if max_cycles and cycle >= max_cycles:
                break

            time.sleep(self.sleep_interval)

        return results

    # ============================================================
    # ✅ PRIORITY-BASED SCHEDULING
    # ============================================================

    def run_priority(self, context, max_cycles=None):
        """
        Prioritize queues based on size (largest first).
        """

        cycle = 0
        results = []

        while True:
            queues_snapshot = self.queue_runtime.snapshot()

            # Sort by queue size (descending)
            sorted_queues = sorted(
                queues_snapshot.items(),
                key=lambda x: x[1],
                reverse=True,
            )

            for queue_name, _ in sorted_queues:
                result = self.worker_runtime.run_once(queue_name, context)
                results.append(result)

            cycle += 1

            if max_cycles and cycle >= max_cycles:
                break

            time.sleep(self.sleep_interval)

        return results

    # ============================================================
    # ✅ BACKPRESSURE-AWARE SCHEDULING
    # ============================================================

    def run_with_backpressure(self, context, threshold=1000, max_cycles=None):
        """
        Adjust scheduling when queues are overloaded.
        """

        cycle = 0
        results = []

        while True:
            pressure = self.queue_runtime.check_backpressure(threshold)

            queue_names = self.queue_runtime.list_queues()

            for queue_name in queue_names:
                if queue_name in pressure:
                    # prioritize overloaded queue
                    result = self.worker_runtime.run_once(queue_name, context)
                    results.append(result)

            # process normal queues afterward
            for queue_name in queue_names:
                if queue_name not in pressure:
                    result = self.worker_runtime.run_once(queue_name, context)
                    results.append(result)

            cycle += 1

            if max_cycles and cycle >= max_cycles:
                break

            time.sleep(self.sleep_interval)

        return results

    # ============================================================
    # ✅ ADAPTIVE SCHEDULING
    # ============================================================

    def run_adaptive(self, context, adaptive_manager, max_cycles=None):
        """
        Scheduling influenced by adaptive layer decisions.
        """

        cycle = 0
        results = []

        while True:
            # Get adaptive decisions
            adaptation = adaptive_manager.evaluate(context.telemetry)

            # Apply safe policy updates
            context.policy.update(adaptation)

            queue_names = self.queue_runtime.list_queues()

            # dynamic prioritization (e.g., larger queues first)
            queue_sizes = self.queue_runtime.snapshot()

            sorted_queues = sorted(
                queue_names,
                key=lambda q: queue_sizes.get(q, 0),
                reverse=True,
            )

            for queue_name in sorted_queues:
                result = self.worker_runtime.run_once(queue_name, context)
                results.append(result)

            cycle += 1

            if max_cycles and cycle >= max_cycles:
                break

            time.sleep(self.sleep_interval)

        return results

    # ============================================================
    # ✅ TARGETED QUEUE SCHEDULING
    # ============================================================

    def run_queue(self, queue_name, context, max_cycles=None):
        """
        Run scheduler for a specific queue only.
        """

        cycle = 0
        results = []

        while True:
            result = self.worker_runtime.run_once(queue_name, context)
            results.append(result)

            cycle += 1

            if max_cycles and cycle >= max_cycles:
                break

            if result["status"] == "idle":
                break

            time.sleep(self.sleep_interval)

        return results

    # ============================================================
    # ✅ DEBUG / TRACE
    # ============================================================

    def trace(self):
        """
        Returns queue-level execution state.
        """

        return {
            "queues": self.queue_runtime.snapshot(),
            "total_events": self.queue_runtime.total_size(),
        }