# afritech/trace/trace_reconstructor.py

"""
AfriTech Trace Reconstructor
============================

Purpose:
Reconstruct execution deterministically from a TRACE.

Responsibilities:
- rebuild execution flow
- respect causal dependencies (linear chain + DAG)
- verify event hash integrity
- support replay consistency checks
- expose causal views (sequence, graph, lineage)
- emit replay witnesses required by constitutional law

This is the runtime bridge between:
TRACE → REPLAY → PROOF
"""

from __future__ import annotations

from typing import Dict, Any, List, Callable, Set

from afritech.trace.trace_hash import compute_event_hash
from afritech.trace.trace_validator import validate_trace


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class TraceReconstructionError(Exception):
    """Raised when trace reconstruction or replay fails"""
    pass


# -----------------------------------------------------------------
# RECONSTRUCTOR
# -----------------------------------------------------------------

class TraceReconstructor:
    """
    Deterministic trace reconstructor.

    This class NEVER executes real logic.
    It only reconstructs and verifies causality.
    """

    # =============================================================
    # ENTRYPOINT — LINEAR RECONSTRUCTION
    # =============================================================

    @classmethod
    def reconstruct(cls, trace: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Reconstruct execution steps from a trace.

        Returns:
            Ordered list of reconstructed execution steps.
        """

        cls._basic_validate(trace)
        validate_trace(trace)

        events = trace["events"]

        cls._validate_event_hashes(events)

        execution_sequence: List[Dict[str, Any]] = []

        for event in events:
            execution_sequence.append(
                cls._reconstruct_event(event)
            )

        return execution_sequence

    # =============================================================
    # EVENT RECONSTRUCTION
    # =============================================================

    @staticmethod
    def _reconstruct_event(event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a TRACE event into a replayable execution step.

        NOTE:
        This does NOT re-execute logic.
        """

        return {
            "index": event["index"],
            "step": event["step"],
            "payload": event.get("payload"),
            "result": event.get("result"),
            "depends_on": event.get("depends_on", []),
            "authority_context_hash": event["authority_context_hash"],
            "event_hash": event["event_hash"],
            "surface": event.get("surface"),
        }

    # =============================================================
    # REPLAY VERIFICATION (DETERMINISTIC CHECK)
    # =============================================================

    @classmethod
    def verify_replay(
        cls,
        trace: Dict[str, Any],
        execution_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> bool:
        """
        Deterministically replay execution against a provided pure function.
        """

        cls._basic_validate(trace)
        validate_trace(trace)

        cls._validate_event_hashes(trace["events"])

        for event in trace["events"]:
            payload = event.get("payload")
            expected = event.get("result")

            if payload is None:
                continue  # non-execution event

            actual = execution_fn(payload)

            if actual != expected:
                raise TraceReconstructionError(
                    "replay_output_mismatch"
                )

        return True

    # =============================================================
    # GRAPH VIEW (DAG)
    # =============================================================

    @classmethod
    def reconstruct_graph(
        cls,
        trace: Dict[str, Any],
    ) -> Dict[int, List[int]]:
        """
        Build dependency graph from TRACE.
        """

        cls._basic_validate(trace)

        graph: Dict[int, List[int]] = {}

        for event in trace["events"]:
            graph[event["index"]] = list(
                event.get("depends_on", [])
            )

        return graph

    # =============================================================
    # LINEAGE (TRANSITIVE DEPENDENCIES)
    # =============================================================

    @classmethod
    def lineage(
        cls,
        trace: Dict[str, Any],
        index: int,
    ) -> List[int]:
        """
        Return full dependency lineage for an event.
        """

        cls._basic_validate(trace)

        events = trace["events"]

        if index < 0 or index >= len(events):
            raise TraceReconstructionError(
                "invalid_event_index"
            )

        visited: Set[int] = set()

        def walk(i: int):
            for dep in events[i].get("depends_on", []):
                if dep not in visited:
                    visited.add(dep)
                    walk(dep)

        walk(index)

        return sorted(visited)

    # =============================================================
    # EVENT HASH CONSISTENCY
    # =============================================================

    @staticmethod
    def _validate_event_hashes(
        events: List[Dict[str, Any]]
    ) -> None:
        """
        Ensure every event_hash matches recomputation.
        """

        for event in events:
            recomputed = compute_event_hash(event)

            if event.get("event_hash") != recomputed:
                raise TraceReconstructionError(
                    "event_hash_mismatch"
                )

    # =============================================================
    # BASIC STRUCTURE VALIDATION
    # =============================================================

    @staticmethod
    def _basic_validate(trace: Dict[str, Any]) -> None:
        if not isinstance(trace, dict):
            raise TraceReconstructionError(
                "invalid_trace_type"
            )

        if "events" not in trace:
            raise TraceReconstructionError(
                "missing_events"
            )

        if not isinstance(trace["events"], list):
            raise TraceReconstructionError(
                "invalid_events_structure"
            )

        if len(trace["events"]) == 0:
            raise TraceReconstructionError(
                "empty_trace"
            )

    # =============================================================
    # STRICT REPLAY (FULL COMPARISON)
    # =============================================================

    @classmethod
    def strict_replay(
        cls,
        trace: Dict[str, Any],
        execution_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Perform full strict replay and return comparison summary.
        """

        cls.verify_replay(trace, execution_fn)

        reconstructed: List[Dict[str, Any]] = []

        for event in trace["events"]:
            payload = event.get("payload")

            if payload is None:
                continue

            out = execution_fn(payload)

            reconstructed.append(
                {
                    "step": event["step"],
                    "payload": payload,
                    "output": out,
                }
            )

        return {
            "status": "MATCH",
            "reconstructed": reconstructed,
        }


# -----------------------------------------------------------------
# FUNCTION EXPORT (REPLAY COMPATIBILITY)
# -----------------------------------------------------------------

def reconstruct_trace(
    *,
    epoch_history,
    registry,
):
    """
    Public replay entrypoint.

    This reconstructs a TRACE object (not just steps)
    for replay verification.

    This bridges:
    EPOCH → TRACE → VALIDATION → TRANSCRIPT
    """

    events: List[Dict[str, Any]] = []
    surface_set: Set[str] = set()

    for epoch in epoch_history:
        trace_events = epoch.get("trace_events", [])

        if not isinstance(trace_events, list):
            raise TraceReconstructionError(
                "invalid trace_events structure"
            )

        for event in trace_events:
            events.append(event)

            # -----------------------------------------------------
            # CLOSED-WORLD REPLAY WITNESS (I8)
            # -----------------------------------------------------
            surface = event.get("surface")
            if surface is not None:
                surface_set.add(surface)

    if not events:
        raise TraceReconstructionError("no_trace_events_found")

    # Build reconstructed trace / transcript
    trace: Dict[str, Any] = {
        "trace_id": "REPLAY_TRACE",
        "epoch_id": registry.get("epoch", {}).get("current"),
        "request_hash": "REPLAY_RECONSTRUCTION",
        "events": events,

        # ---------------------------------------------------------
        # REPLAY WITNESSES (REQUIRED BY SEMANTIC LAW)
        # ---------------------------------------------------------
        "execution_trace_surface_set": sorted(surface_set),
    }

    # Compute root
    from afritech.trace.trace_hash import compute_trace_root

    trace["trace_root_hash"] = compute_trace_root(events)

    return trace