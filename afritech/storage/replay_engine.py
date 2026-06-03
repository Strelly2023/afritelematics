"""Replay engine for MVP production pipeline event records."""

from __future__ import annotations

from typing import Dict, Any

from afritech.core.engine import execute
from afritech.storage.event_schema import EventRecord
from afritech.execution.worker.types import WorkerResult


class ReplayEngineError(RuntimeError):
    """Raised when replay execution fails or diverges."""


# ---------------------------------------------------------
# CORE REPLAY EXECUTION
# ---------------------------------------------------------

def replay_event(event: EventRecord) -> WorkerResult:
    """
    Replay a single event deterministically.

    HARD GUARANTEES:
    - Same input → same output → same hash
    - No divergence tolerated
    - Reconstructed result must match original record
    """

    if event is None:
        raise ReplayEngineError("EventRecord is required for replay")

    if event.normalized_input is None:
        raise ReplayEngineError("EventRecord missing normalized_input")

    if event.replay_hash is None:
        raise ReplayEngineError("EventRecord missing replay_hash")

    # ---------------------------------------------------------
    # RE-EXECUTE (DETERMINISTIC)
    # ---------------------------------------------------------
    output = execute(event.normalized_input)

    if output is None:
        raise ReplayEngineError("Execution returned None during replay")

    # ---------------------------------------------------------
    # RECOMPUTE HASH
    # ---------------------------------------------------------
    recomputed_hash = EventRecord.generate_hash(output)

    # ---------------------------------------------------------
    # STRICT EQUIVALENCE CHECK (CRITICAL)
    # ---------------------------------------------------------
    if recomputed_hash != event.replay_hash:
        raise ReplayEngineError(
            "Replay divergence detected: "
            f"{recomputed_hash} != {event.replay_hash}"
        )

    # ---------------------------------------------------------
    # RECONSTRUCT WORKER RESULT (CANONICAL FORM)
    # ---------------------------------------------------------
    return WorkerResult(
        request_id=event.request_id,
        partition_id=event.partition_id,
        outputs=output,
        trace=event.trace,
        replay_hash=recomputed_hash,
    )


# ---------------------------------------------------------
# BULK REPLAY (OPTIONAL UTILITY)
# ---------------------------------------------------------

def replay_events(events: list[EventRecord]) -> list[WorkerResult]:
    """
    Replay multiple events deterministically.

    FAIL-FAST:
    - Any divergence aborts the entire replay process
    """

    results: list[WorkerResult] = []

    for idx, event in enumerate(events):
        try:
            result = replay_event(event)
            results.append(result)
        except Exception as exc:
            raise ReplayEngineError(
                f"Replay failed at index {idx}: {exc}"
            ) from exc

    return results


# ---------------------------------------------------------
# STRICT REPLAY COMPARISON (OPTIONAL)
# ---------------------------------------------------------

def compare_replay(
    original: WorkerResult,
    replayed: WorkerResult,
) -> None:
    """
    Enforce strict replay equivalence between original and replayed results.
    """

    if not isinstance(original, WorkerResult):
        raise ReplayEngineError("Original result is not WorkerResult")

    if not isinstance(replayed, WorkerResult):
        raise ReplayEngineError("Replayed result is not WorkerResult")

    # ✅ HASH CHECK
    if original.replay_hash != replayed.replay_hash:
        raise ReplayEngineError(
            "Replay hash mismatch detected"
        )

    # ✅ STRUCTURAL CHECK
    if not original.is_replay_equivalent(replayed):
        raise ReplayEngineError(
            "Replay structural mismatch detected"
        )


# ---------------------------------------------------------
# STRICT ENTRYPOINT FOR CI OR PIPELINE
# ---------------------------------------------------------

def require_replay_match(event: EventRecord) -> WorkerResult:
    """
    Replay event and enforce exact match.
    Shortcut helper for strict pipelines.
    """
    result = replay_event(event)

    # No additional comparison needed because replay_event already guarantees hash equivalence
    return result
