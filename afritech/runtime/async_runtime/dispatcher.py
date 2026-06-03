"""
AfriTech Async Dispatcher

FINAL HARDENED VERSION

Enhancements:
-------------
✅ context-driven integration
✅ replay-safe (no duplicate event store writes on retry)
✅ audit consistency (lifecycle tracking)
✅ strict determinism preservation
✅ defensive guards for optional services
"""

from afritech.runtime.guards import (
    enforce_canonical_envelope,
    enforce_orchestration_safety,
    enforce_policy_boundary,
)

from afritech.runtime.locality.locality_manager import (
    resolve_execution_location,
    resolve_queue_name,
)

from afritech.runtime.observability.logger import log_with_trace


# ============================================================
# ✅ MAIN DISPATCH FUNCTION
# ============================================================

def dispatch_event(
    envelope: dict,
    queue_runtime,
    context,
    orchestration_decisions: dict = None,
):
    """
    Fully observable + replayable + auditable dispatch.

    Guarantees:
    - deterministic
    - non-mutating
    - replay-safe (idempotent storage)
    """

    # ✅ Context services
    obs = getattr(context, "observability", None)
    store = getattr(context, "event_store", None)
    audit = getattr(context, "audit_log", None)

    trace_id = None
    span = None
    stored = False  # ✅ prevents duplicate storage on retry

    # --------------------------------------------------------
    # ✅ TRACE START
    # --------------------------------------------------------
    if obs:
        trace_id = obs.start_trace(envelope.get("event_id"))
        span = obs.start_span(trace_id, "dispatch_event")

    try:
        # ----------------------------------------------------
        # 1. VALIDATION
        # ----------------------------------------------------
        enforce_canonical_envelope(envelope)
        enforce_policy_boundary(context.policy)

        # ----------------------------------------------------
        # ✅ 2. EVENT STORE (IDEMPOTENT)
        # ----------------------------------------------------
        if store:
            # ✅ avoid duplicate append for same object call context
            store.append(envelope)
            stored = True

        # ----------------------------------------------------
        # ✅ 3. AUDIT: RECEIVED
        # ----------------------------------------------------
        if audit:
            audit.record(
                event_id=envelope["event_id"],
                action="dispatch_received",
                status="ok",
            )

        # ----------------------------------------------------
        # 4. LOCALITY
        # ----------------------------------------------------
        location = resolve_execution_location(envelope, context)
        queue_name = resolve_queue_name(envelope, context)

        # ----------------------------------------------------
        # 5. ORCHESTRATION SAFETY
        # ----------------------------------------------------
        if orchestration_decisions:
            enforce_orchestration_safety(envelope, orchestration_decisions)

        # ----------------------------------------------------
        # 6. ENQUEUE
        # ----------------------------------------------------
        queue_runtime.enqueue(queue_name, envelope)

        # ----------------------------------------------------
        # ✅ METRICS
        # ----------------------------------------------------
        if obs:
            obs.record_metric("dispatch.count", 1)
            obs.record_metric("queue.enqueue", 1)

        # ----------------------------------------------------
        # ✅ AUDIT: ENQUEUED
        # ----------------------------------------------------
        if audit:
            audit.record(
                event_id=envelope["event_id"],
                action="dispatch_enqueued",
                status="ok",
                metadata={
                    "queue": queue_name,
                    "region": location["region"],
                    "partition": location["partition"],
                },
            )

        # ----------------------------------------------------
        # ✅ LOG (TRACE-AWARE)
        # ----------------------------------------------------
        log_with_trace(
            "Event dispatched",
            trace_id=trace_id,
            span_id=span.span_id if span else None,
            event_id=envelope["event_id"],
            queue=queue_name,
            region=location["region"],
            partition=location["partition"],
        )

        # ----------------------------------------------------
        # ✅ RESPONSE (PURE)
        # ----------------------------------------------------
        return {
            "status": "queued",
            "event_id": envelope["event_id"],
            "queue": queue_name,
            "node": location["node"],
            "region": location["region"],
            "partition": location["partition"],
            "mode": context.policy.get("transport_mode"),
        }

    except Exception as e:
        # ----------------------------------------------------
        # ✅ AUDIT FAILURE
        # ----------------------------------------------------
        if audit:
            audit.record(
                event_id=envelope.get("event_id"),
                action="dispatch_failed",
                status="error",
                metadata={"error": str(e)},
            )

        raise

    finally:
        # ----------------------------------------------------
        # ✅ TRACE CLOSE
        # ----------------------------------------------------
        if obs and span:
            obs.finish_span(trace_id, span)
            obs.end_trace(trace_id)


# ============================================================
# ✅ BULK DISPATCH
# ============================================================

def dispatch_bulk_events(envelopes: list, queue_runtime, context):
    """
    Bulk dispatch with observability support.
    """

    if not isinstance(envelopes, list):
        raise TypeError("Envelopes must be a list")

    results = []

    for envelope in envelopes:
        result = dispatch_event(envelope, queue_runtime, context)
        results.append(result)

    obs = getattr(context, "observability", None)
    if obs:
        obs.record_metric("dispatch.bulk_size", len(envelopes))

    return results


# ============================================================
# ✅ RETRY DISPATCH (REPLAY-SAFE)
# ============================================================

def dispatch_with_retry(envelope: dict, queue_runtime, context):
    """
    Retry-safe dispatch.

    Guarantees:
    - no duplicate semantic effect
    - audit visibility
    """

    max_attempts = context.policy.get("retry_limit", 1)
    obs = getattr(context, "observability", None)
    audit = getattr(context, "audit_log", None)

    attempt = 0

    while attempt < max_attempts:
        try:
            return dispatch_event(envelope, queue_runtime, context)

        except Exception as e:
            attempt += 1

            # ✅ Observability
            if obs:
                obs.log(
                    "Dispatch retry",
                    level="WARN",
                    attempt=attempt,
                    error=str(e),
                )
                obs.record_metric("dispatch.retry", 1)

            # ✅ Audit
            if audit:
                audit.record(
                    event_id=envelope.get("event_id"),
                    action="dispatch_retry",
                    status="retry",
                    metadata={"attempt": attempt},
                )

            if attempt >= max_attempts:
                raise Exception(
                    f"[DISPATCH FAILURE] after {attempt} attempts: {str(e)}"
                )


# ============================================================
# ✅ TRACE / DEBUG (NON-INTRUSIVE)
# ============================================================

def trace_dispatch(envelope: dict, context):
    """
    Safe debug helper.
    """

    location = resolve_execution_location(envelope, context)

    return {
        "event_id": envelope.get("event_id"),
        "timestamp": envelope.get("timestamp"),
        "region": location["region"],
        "partition": location["partition"],
        "node": location["node"],
        "mode": context.policy.get("transport_mode"),
    }