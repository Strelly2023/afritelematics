"""
afritech.trace.trace_reconstructor
==================================

Canonical deterministic trace reconstruction surface.

This surface governs:
- deterministic replay reconstruction
- replay-safe trace validation
- causal dependency reconstruction
- lineage reconstruction
- replay equivalence verification
- closed-world trace topology validation
- invariant-preserving replay semantics

This surface is constitutionally classified as:

    IMPLEMENTATION_STATE = "PLANNED"

Meaning:
- ontology-visible
- architecturally declared
- replay-significant
- constitutionally recognized

But NOT yet fully operationally admissible for:
- global replay equivalence
- full transcript reconstruction
- complete mutation lineage reconstruction
- constitutional proof closure

This surface MUST remain:
- deterministic
- replay-safe
- observer-independent
- ontology-safe
- closed-world aligned

Filesystem structure must never independently define
constitutional identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Set

from afritech.trace.trace_hash import (
    compute_event_hash,
    compute_trace_root,
)

from afritech.trace.trace_validator import (
    validate_trace,
)


# ============================================================
# CONSTITUTIONAL IDENTITY
# ============================================================

CANONICAL_IDENTITY = (
    "afritech.trace.trace_reconstructor"
)

IMPLEMENTATION_STATE = "PLANNED"

REPLAY_ADMISSIBLE = False

PROOF_ADMISSIBLE = False

RUNTIME_ADMISSIBLE = False

DETERMINISTIC_EXECUTION = True

CLOSED_WORLD_ALIGNED = True

OBSERVER_INDEPENDENT = True

REPLAY_SAFE = True


# ============================================================
# EXCEPTIONS
# ============================================================

class TraceReconstructionError(Exception):
    """
    Raised when deterministic trace reconstruction fails.
    """


class ReplayEquivalenceError(
    TraceReconstructionError,
):
    """
    Raised when replay equivalence diverges.
    """


class ClosedWorldViolationError(
    TraceReconstructionError,
):
    """
    Raised when undeclared surfaces appear.
    """


# ============================================================
# RECONSTRUCTION RESULT
# ============================================================

@dataclass(frozen=True)
class ReconstructionSummary:

    deterministic: bool

    replay_safe: bool

    event_count: int

    trace_root_hash: str

    execution_surface_set: List[str]


# ============================================================
# TRACE RECONSTRUCTOR
# ============================================================

class TraceReconstructor:
    """
    Deterministic replay-safe trace reconstructor.

    IMPORTANT:
    This surface NEVER executes application logic.

    It ONLY:
    - reconstructs topology
    - validates replay structure
    - validates deterministic equivalence
    - validates causal dependencies

    This preserves:
    - replay safety
    - invariant preservation
    - observer independence
    - closed-world execution semantics
    """

    # ========================================================
    # LINEAR RECONSTRUCTION
    # ========================================================

    @classmethod
    def reconstruct(
        cls,
        trace: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Deterministically reconstruct execution sequence.

        NOTE:
        Reconstruction is structural only.
        No business logic is executed.
        """

        cls._basic_validate(trace)

        validate_trace(trace)

        events = trace["events"]

        cls._validate_event_hashes(events)

        execution_sequence: List[
            Dict[str, Any]
        ] = []

        for event in events:

            execution_sequence.append(

                cls._reconstruct_event(event)

            )

        return execution_sequence

    # ========================================================
    # EVENT RECONSTRUCTION
    # ========================================================

    @staticmethod
    def _reconstruct_event(
        event: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert TRACE event into deterministic replay step.
        """

        return {

            "index":
                event["index"],

            "step":
                event["step"],

            "payload":
                event.get("payload"),

            "result":
                event.get("result"),

            "depends_on":
                event.get("depends_on", []),

            "authority_context_hash":
                event[
                    "authority_context_hash"
                ],

            "event_hash":
                event["event_hash"],

            "surface":
                event.get("surface"),
        }

    # ========================================================
    # REPLAY VERIFICATION
    # ========================================================

    @classmethod
    def verify_replay(
        cls,
        trace: Dict[str, Any],
        execution_fn: Callable[
            [Dict[str, Any]],
            Dict[str, Any],
        ],
    ) -> bool:
        """
        Deterministically verify replay equivalence.

        IMPORTANT:
        This validates equivalence only.
        It does NOT grant constitutional legitimacy.
        """

        cls._basic_validate(trace)

        validate_trace(trace)

        cls._validate_event_hashes(
            trace["events"]
        )

        for event in trace["events"]:

            payload = event.get(
                "payload"
            )

            expected = event.get(
                "result"
            )

            if payload is None:
                continue

            actual = execution_fn(payload)

            if actual != expected:

                raise ReplayEquivalenceError(
                    "replay_output_mismatch"
                )

        return True

    # ========================================================
    # DAG RECONSTRUCTION
    # ========================================================

    @classmethod
    def reconstruct_graph(
        cls,
        trace: Dict[str, Any],
    ) -> Dict[int, List[int]]:
        """
        Build deterministic dependency graph.
        """

        cls._basic_validate(trace)

        graph: Dict[
            int,
            List[int]
        ] = {}

        for event in trace["events"]:

            graph[event["index"]] = list(

                event.get(
                    "depends_on",
                    []
                )

            )

        return graph

    # ========================================================
    # LINEAGE
    # ========================================================

    @classmethod
    def lineage(
        cls,
        trace: Dict[str, Any],
        index: int,
    ) -> List[int]:
        """
        Deterministically reconstruct dependency lineage.
        """

        cls._basic_validate(trace)

        events = trace["events"]

        if index < 0 or index >= len(events):

            raise TraceReconstructionError(
                "invalid_event_index"
            )

        visited: Set[int] = set()

        def walk(i: int):

            for dep in events[i].get(
                "depends_on",
                [],
            ):

                if dep not in visited:

                    visited.add(dep)

                    walk(dep)

        walk(index)

        return sorted(visited)

    # ========================================================
    # HASH VALIDATION
    # ========================================================

    @staticmethod
    def _validate_event_hashes(
        events: List[Dict[str, Any]]
    ) -> None:
        """
        Deterministically validate event hashes.
        """

        for event in events:

            recomputed = compute_event_hash(
                event
            )

            if (
                event.get("event_hash")
                != recomputed
            ):

                raise TraceReconstructionError(
                    "event_hash_mismatch"
                )

    # ========================================================
    # CLOSED-WORLD SURFACE VALIDATION
    # ========================================================

    @staticmethod
    def _validate_surface_set(
        surfaces: Set[str],
    ) -> None:
        """
        Validate closed-world surface admissibility.
        """

        forbidden = {

            "",
            None,
            "dynamic",
            "reflection",
            "runtime_discovery",

        }

        for surface in surfaces:

            if surface in forbidden:

                raise ClosedWorldViolationError(

                    f"forbidden surface: "
                    f"{surface}"

                )

    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    @staticmethod
    def _basic_validate(
        trace: Dict[str, Any],
    ) -> None:

        if not isinstance(trace, dict):

            raise TraceReconstructionError(
                "invalid_trace_type"
            )

        if "events" not in trace:

            raise TraceReconstructionError(
                "missing_events"
            )

        if not isinstance(
            trace["events"],
            list,
        ):

            raise TraceReconstructionError(
                "invalid_events_structure"
            )

        if len(trace["events"]) == 0:

            raise TraceReconstructionError(
                "empty_trace"
            )

    # ========================================================
    # STRICT REPLAY
    # ========================================================

    @classmethod
    def strict_replay(
        cls,
        trace: Dict[str, Any],
        execution_fn: Callable[
            [Dict[str, Any]],
            Dict[str, Any],
        ],
    ) -> Dict[str, Any]:
        """
        Deterministic strict replay comparison.
        """

        cls.verify_replay(
            trace,
            execution_fn,
        )

        reconstructed = []

        for event in trace["events"]:

            payload = event.get(
                "payload"
            )

            if payload is None:
                continue

            output = execution_fn(
                payload
            )

            reconstructed.append({

                "step":
                    event["step"],

                "payload":
                    payload,

                "output":
                    output,
            })

        return {

            "status":
                "MATCH",

            "deterministic":
                True,

            "replay_safe":
                True,

            "reconstructed":
                reconstructed,
        }


# ============================================================
# REPLAY ENTRYPOINT
# ============================================================

def reconstruct_trace(
    *,
    epoch_history,
    registry,
):
    """
    Deterministically reconstruct replay TRACE object.

    Bridges:

        EPOCH
            → TRACE
            → VALIDATION
            → REPLAY
            → TRANSCRIPT
    """

    events: List[
        Dict[str, Any]
    ] = []

    surface_set: Set[str] = set()

    for epoch in epoch_history:

        trace_events = epoch.get(
            "trace_events",
            [],
        )

        if not isinstance(
            trace_events,
            list,
        ):

            raise TraceReconstructionError(
                "invalid_trace_events_structure"
            )

        for event in trace_events:

            events.append(event)

            surface = event.get(
                "surface"
            )

            if surface is not None:

                surface_set.add(surface)

    if not events:

        raise TraceReconstructionError(
            "no_trace_events_found"
        )

    TraceReconstructor._validate_surface_set(
        surface_set
    )

    trace: Dict[str, Any] = {

        "trace_id":
            "REPLAY_TRACE",

        "epoch_id":
            registry.get(
                "epoch",
                {},
            ).get("current"),

        "request_hash":
            "REPLAY_RECONSTRUCTION",

        "events":
            events,

        # -----------------------------------------------
        # CLOSED-WORLD REPLAY WITNESS
        # -----------------------------------------------

        "execution_trace_surface_set":
            sorted(surface_set),
    }

    trace["trace_root_hash"] = (

        compute_trace_root(events)

    )

    return trace


# ============================================================
# RECONSTRUCTION SUMMARY
# ============================================================

def summarize_trace(
    trace: Dict[str, Any],
) -> ReconstructionSummary:
    """
    Produce deterministic replay summary.
    """

    events = trace["events"]

    surfaces = sorted({

        event.get("surface")

        for event in events

        if event.get("surface") is not None

    })

    return ReconstructionSummary(

        deterministic=True,

        replay_safe=True,

        event_count=len(events),

        trace_root_hash=trace[
            "trace_root_hash"
        ],

        execution_surface_set=surfaces,
    )