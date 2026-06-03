"""
AfriTech Worker Runtime

PURPOSE:
--------
Executes queued events in a controlled, non-blocking manner.

Responsibilities:
- Pull events from queue
- Execute in batches (policy-driven)
- Preserve deterministic execution
- Enforce guards at execution boundary
- Support adaptive behavior (batching, retries)
- Provide full observability

CRITICAL LAW:
-------------
Worker MAY:
- execute events
- batch events
- retry execution

Worker may NOT:
- mutate event semantics
- reorder events improperly
- define truth or validation
"""

from afritech.runtime.async_runtime.batch_processor import process_batch
from afritech.runtime.guards import (
    enforce_event_integrity,
    enforce_async_safety,
)

from afritech.runtime.observability.span import Span
from afritech.runtime.observability.logger import log_with_trace


class WorkerRuntime:
    def __init__(self, queue_runtime):
        self.queue_runtime = queue_runtime

    # ============================================================
    # ✅ SINGLE EXECUTION CYCLE
    # ============================================================

    def run_once(self, queue_name: str, context):
        """
        Executes one batch from a queue with full observability.
        """

        obs = getattr(context, "observability", None)
        trace_id = None
        span = None

        # --------------------------------------------------------
        # ✅ TRACE START
        # --------------------------------------------------------
        if obs:
            trace_id = obs.start_trace(f"worker:{queue_name}")
            span = obs.start_span(trace_id, "worker_run_once")

        try:
            batch_size = context.policy.get("batch_size", 1)

            # --------------------------------------------------------
            # Dequeue
            # --------------------------------------------------------
            events = self.queue_runtime.dequeue_batch(queue_name, batch_size)

            if not events:
                return {
                    "status": "idle",
                    "queue": queue_name,
                    "processed": 0,
                }

            # ✅ Metric
            if obs:
                obs.record_metric("worker.batch_size", len(events))

            # --------------------------------------------------------
            # Preserve originals
            # --------------------------------------------------------
            original_events = [dict(e) for e in events]

            # --------------------------------------------------------
            # Execute
            # --------------------------------------------------------
            process_batch(events, context)

            # --------------------------------------------------------
            # Guard enforcement
            # --------------------------------------------------------
            for original, processed in zip(original_events, events):
                enforce_event_integrity(original, processed)
                enforce_async_safety(original, processed)

            # ✅ Metrics
            if obs:
                obs.record_metric("worker.processed", len(events))

            # ✅ Logging
            log_with_trace(
                "Batch processed",
                trace_id=trace_id,
                span_id=span.span_id if span else None,
                queue=queue_name,
                processed=len(events),
            )

            return {
                "status": "processed",
                "queue": queue_name,
                "processed": len(events),
            }

        finally:
            # --------------------------------------------------------
            # ✅ TRACE END
            # --------------------------------------------------------
            if obs and span:
                obs.finish_span(trace_id, span)
                obs.end_trace(trace_id)

    # ============================================================
    # ✅ LOOP EXECUTION
    # ============================================================

    def run_loop(self, queue_names: list, context, max_cycles=None):
        cycle = 0
        results = []

        while True:
            for queue_name in queue_names:
                result = self.run_once(queue_name, context)
                results.append(result)

            cycle += 1

            if max_cycles and cycle >= max_cycles:
                break

        return results

    # ============================================================
    # ✅ FULL QUEUE EXECUTION
    # ============================================================

    def run_queue(self, queue_name: str, context, max_batches=None):
        batch_count = 0
        results = []

        while True:
            result = self.run_once(queue_name, context)

            if result["status"] == "idle":
                break

            results.append(result)
            batch_count += 1

            if max_batches and batch_count >= max_batches:
                break

        return results

    # ============================================================
    # ✅ ADAPTIVE EXECUTION
    # ============================================================

    def run_adaptive_cycle(self, queue_name: str, context, adaptive_manager):
        """
        Executes one cycle with adaptive optimization.
        """

        obs = getattr(context, "observability", None)

        # --------------------------------------------------------
        # Adaptive evaluation
        # --------------------------------------------------------
        result = adaptive_manager.evaluate(context)

        load_state = result.get("load_state")

        if obs:
            obs.record_metric("adaptive.cycle", 1)
            obs.log("Adaptive evaluation", load_state=load_state)

        execution_result = self.run_once(queue_name, context)

        return {
            "execution": execution_result,
            "adaptive": {
                "load_state": load_state,
                "policy": dict(context.policy),
            },
        }

    # ============================================================
    # ✅ RETRY EXECUTION
    # ============================================================

    def run_with_retry(self, queue_name: str, context):
        """
        Retry-safe execution.
        """

        max_attempts = context.policy.get("retry_limit", 1)
        attempt = 0

        obs = getattr(context, "observability", None)

        while attempt < max_attempts:
            try:
                return self.run_once(queue_name, context)

            except Exception as e:
                attempt += 1

                if obs:
                    obs.log(
                        "Worker retry",
                        level="WARN",
                        attempt=attempt,
                        error=str(e),
                    )
                    obs.record_metric("worker.retry", 1)

                if attempt >= max_attempts:
                    raise Exception(
                        f"[WORKER FAILURE] after {attempt} attempts: {str(e)}"
                    )

    # ============================================================
    # ✅ BALANCED EXECUTION
    # ============================================================

    def run_balanced(self, queue_names: list, context):
        results = []

        for queue_name in queue_names:
            result = self.run_once(queue_name, context)
            results.append(result)

        return results

    # ============================================================
    # ✅ UNTIL IDLE
    # ============================================================

    def run_until_idle(self, queue_names: list, context, max_cycles=100):
        cycle = 0

        obs = getattr(context, "observability", None)

        while cycle < max_cycles:
            active = False

            for queue_name in queue_names:
                result = self.run_once(queue_name, context)

                if result["status"] != "idle":
                    active = True

            if not active:
                break

            cycle += 1

        if obs:
            obs.record_metric("worker.cycles", cycle)

        return {"status": "drained", "cycles": cycle}

    # ============================================================
    # ✅ DEBUG
    # ============================================================

    def trace_execution(self, queue_name: str):
        return {
            "queue": queue_name,
            "pending": self.queue_runtime.get_queue_length(queue_name),
        }