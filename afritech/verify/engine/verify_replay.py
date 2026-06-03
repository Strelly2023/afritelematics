"""
afritech.verify.engine.verify_replay

Canonical replay verification engine.

This is the SINGLE SOURCE OF TRUTH for:

- deterministic replay validation
- execution vs replay equivalence
- trace reconstruction equivalence
- WorkerResult validation
"""

from __future__ import annotations

from typing import Iterable

from afritech.execution.worker.types import WorkerResult
from afritech.storage.event_schema import EventRecord
from afritech.storage.replay_engine import replay_event
from afritech.trace.trace_reconstructor import TraceReconstructor


# ============================================================
# EXCEPTIONS
# ============================================================

class VerifyReplayError(RuntimeError):
    pass


# ============================================================
# EVENT-LEVEL VERIFICATION
# ============================================================

def verify_event_replay(event: EventRecord) -> WorkerResult:
    """
    Verify replay for a single event.
    """

    result = replay_event(event)

    # replay_event already enforces hash equality
    return result


# ============================================================
# SEQUENCE VERIFICATION
# ============================================================

def verify_event_sequence(events: Iterable[EventRecord]) -> list[WorkerResult]:
    """
    Verify replay across a sequence of events.
    Fail-fast on first divergence.
    """

    results: list[WorkerResult] = []

    for idx, event in enumerate(events):
        try:
            result = verify_event_replay(event)
            results.append(result)
        except Exception as exc:
            raise VerifyReplayError(
                f"Replay failed at event index {idx}: {exc}"
            ) from exc

    return results


# ============================================================
# WORKER RESULT EQUIVALENCE
# ============================================================

def verify_worker_results(results: Iterable[WorkerResult]) -> None:
    """
    Validate that all WorkerResults are replay-equivalent.
    """

    results_list = list(results)

    if not results_list:
        raise VerifyReplayError("No WorkerResults provided")

    base = results_list[0]

    for idx, r in enumerate(results_list[1:], start=1):

        if not isinstance(r, WorkerResult):
            raise VerifyReplayError(
                f"Invalid WorkerResult at index {idx}"
            )

        if not r.is_replay_equivalent(base):
            raise VerifyReplayError(
                f"Replay divergence detected at index {idx}"
            )


# ============================================================
# TRACE-LEVEL VERIFICATION
# ============================================================

def verify_trace_replay(trace, execution_fn) -> None:
    """
    Verify full trace replay determinism.
    """

    try:
        TraceReconstructor.verify_replay(trace, execution_fn)
    except Exception as exc:
        raise VerifyReplayError(
            f"Trace replay verification failed: {exc}"
        ) from exc


# ============================================================
# FULL SYSTEM VERIFICATION
# ============================================================

def verify_full_replay(
    events: Iterable[EventRecord],
    trace,
    execution_fn,
) -> list[WorkerResult]:
    """
    End-to-end replay verification.

    Pipeline:
    1. replay events
    2. verify worker results
    3. verify trace
    """

    results = verify_event_sequence(events)

    verify_worker_results(results)

    verify_trace_replay(trace, execution_fn)

    return results
