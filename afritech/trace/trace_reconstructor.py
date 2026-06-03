"""afritech.trace.trace_reconstructor"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Set

from afritech.trace.trace_hash import (
    compute_event_hash,
    compute_trace_root,
)

from afritech.trace.trace_validator import validate_trace

from afritech.core.runtime.receipts import (
    build_execution_chain,
    verify_receipt_bundle,
)

from afritech.shared.types import stable_hash


# ============================================================
# EXCEPTIONS
# ============================================================

class TraceReconstructionError(Exception):
    pass


class ReplayEquivalenceError(TraceReconstructionError):
    pass


class ClosedWorldViolationError(TraceReconstructionError):
    pass


# ============================================================
# SUMMARY
# ============================================================

@dataclass(frozen=True)
class ReconstructionSummary:
    deterministic: bool
    replay_safe: bool
    event_count: int
    trace_root_hash: str
    execution_surface_set: List[str]


# ============================================================
# RECONSTRUCTOR
# ============================================================

class TraceReconstructor:

    # ========================================================
    # CORE RECONSTRUCTION
    # ========================================================

    @classmethod
    def reconstruct(cls, trace: Dict[str, Any]) -> List[Dict[str, Any]]:
        cls._basic_validate(trace)
        validate_trace(trace)

        events = cls._enforce_order(trace["events"])

        cls._validate_event_hashes(events)
        cls._validate_trace_root(trace, events)
        cls._validate_surfaces(events)

        return [cls._reconstruct_event(e) for e in events]

    # ========================================================
    # EVENT
    # ========================================================

    @staticmethod
    def _reconstruct_event(event: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "index": event["index"],
            "step": event["step"],
            "payload": event.get("payload"),
            "result": event.get("result"),
            "depends_on": sorted(event.get("depends_on", [])),
            "authority_context_hash": event["authority_context_hash"],
            "event_hash": event["event_hash"],
            "surface": event.get("surface"),
        }

    # ========================================================
    # REPLAY VERIFICATION
    # ========================================================

    @classmethod
    def verify_replay(
        cls,
        trace: Dict[str, Any],
        execution_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> bool:

        cls._basic_validate(trace)
        validate_trace(trace)

        events = cls._enforce_order(trace["events"])

        cls._validate_event_hashes(events)
        cls._validate_trace_root(trace, events)
        cls._validate_surfaces(events)

        for idx, event in enumerate(events):
            payload = event.get("payload")
            expected = event.get("result")

            if payload is None:
                continue

            actual = execution_fn(payload)

            # ✅ canonical equality (critical fix)
            if not cls._canonical_equal(actual, expected):
                raise ReplayEquivalenceError(
                    f"replay_output_mismatch_at_index_{idx}"
                )

        return True

    # ========================================================
    # GRAPH
    # ========================================================

    @classmethod
    def reconstruct_graph(cls, trace: Dict[str, Any]) -> Dict[int, List[int]]:
        cls._basic_validate(trace)

        return {
            e["index"]: sorted(e.get("depends_on", []))
            for e in trace["events"]
        }

    # ========================================================
    # LINEAGE
    # ========================================================

    @classmethod
    def lineage(cls, trace: Dict[str, Any], index: int) -> List[int]:
        cls._basic_validate(trace)

        events = cls._enforce_order(trace["events"])

        if index < 0 or index >= len(events):
            raise TraceReconstructionError("invalid_event_index")

        visited: Set[int] = set()

        def walk(i: int):
            for dep in sorted(events[i].get("depends_on", [])):
                if dep not in visited:
                    visited.add(dep)
                    walk(dep)

        walk(index)
        return sorted(visited)

    # ========================================================
    # HASH VALIDATION
    # ========================================================

    @staticmethod
    def _validate_event_hashes(events: List[Dict[str, Any]]) -> None:
        for event in events:
            if event.get("event_hash") != compute_event_hash(event):
                raise TraceReconstructionError("event_hash_mismatch")

    @staticmethod
    def _validate_trace_root(
        trace: Dict[str, Any],
        events: List[Dict[str, Any]],
    ) -> None:
        expected = trace.get("trace_root_hash")
        actual = compute_trace_root(events)

        if expected != actual:
            raise TraceReconstructionError("trace_root_hash_mismatch")

    # ========================================================
    # ORDER ENFORCEMENT ✅ CRITICAL
    # ========================================================

    @staticmethod
    def _enforce_order(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            return sorted(events, key=lambda e: e["index"])
        except KeyError:
            raise TraceReconstructionError("missing_event_index")

    # ========================================================
    # CLOSED WORLD ✅ CRITICAL
    # ========================================================

    @classmethod
    def _validate_surfaces(cls, events: List[Dict[str, Any]]) -> None:
        surfaces = {
            e.get("surface")
            for e in events
            if e.get("surface") is not None
        }

        forbidden = {
            "",
            None,
            "dynamic",
            "reflection",
            "runtime_discovery",
        }

        for s in surfaces:
            if s in forbidden:
                raise ClosedWorldViolationError(
                    f"forbidden surface: {s}"
                )

    # ========================================================
    # CANONICAL COMPARISON ✅ CRITICAL
    # ========================================================

    @staticmethod
    def _canonical_equal(a: Any, b: Any) -> bool:
        return stable_hash(a) == stable_hash(b)

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _basic_validate(trace: Dict[str, Any]) -> None:
        if not isinstance(trace, dict):
            raise TraceReconstructionError("invalid_trace_type")

        if "events" not in trace:
            raise TraceReconstructionError("missing_events")

        if not isinstance(trace["events"], list):
            raise TraceReconstructionError("invalid_events_structure")

        if not trace["events"]:
            raise TraceReconstructionError("empty_trace")

    # ========================================================
    # STRICT REPLAY
    # ========================================================

    @classmethod
    def strict_replay(
        cls,
        trace: Dict[str, Any],
        execution_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> Dict[str, Any]:

        cls.verify_replay(trace, execution_fn)

        events = cls._enforce_order(trace["events"])

        reconstructed = []

        for idx, event in enumerate(events):
            payload = event.get("payload")

            if payload is None:
                continue

            output = execution_fn(payload)

            reconstructed.append({
                "index": idx,
                "step": event["step"],
                "payload": payload,
                "output": output,
            })

        return {
            "status": "MATCH",
            "deterministic": True,
            "replay_safe": True,
            "reconstructed": reconstructed,
        }

    # ========================================================
    # RECEIPTS
    # ========================================================

    @classmethod
    def reconstruct_receipt_bundle(cls, bundle: Dict[str, Any]) -> Dict[str, Any]:

        if not verify_receipt_bundle(bundle):
            raise TraceReconstructionError("receipt_bundle_invalid")

        transcript = bundle["transcript"]
        mutation_trace = bundle["mutation_trace"]
        receipt = bundle["receipt"]

        execution_chain = build_execution_chain(
            {
                "contract": bundle.get("input_contract"),
                "truth_values": bundle.get("input_truth_values"),
            },
            transcript["steps"],
        )

        replay_hash = stable_hash({
            "program_id": receipt.get("program_id"),
            "decision": receipt.get("decision"),
            "transcript_hash": transcript["transcript_hash"],
            "mutation_trace_hash": mutation_trace["mutation_trace_hash"],
            "execution_chain_hash": execution_chain["execution_chain_hash"],
        })

        if replay_hash != receipt.get("replay_hash"):
            raise ReplayEquivalenceError("replay_hash_mismatch")

        return {
            "status": "RECONSTRUCTED",
            "program_id": receipt.get("program_id"),
            "decision": receipt.get("decision"),
            "execution_chain_hash": execution_chain["execution_chain_hash"],
            "transcript_hash": transcript["transcript_hash"],
            "mutation_trace_hash": mutation_trace["mutation_trace_hash"],
            "replay_hash": replay_hash,
            "receipt_hash": receipt["receipt_hash"],
            "deterministic": True,
            "replay_safe": True,
        }


# ============================================================
# ENTRYPOINT
# ============================================================

def reconstruct_trace(*, epoch_history, registry):

    events: List[Dict[str, Any]] = []
    surfaces: Set[str] = set()

    for epoch in epoch_history:
        for event in epoch.get("trace_events", []):
            events.append(event)
            if event.get("surface"):
                surfaces.add(event["surface"])

    if not events:
        raise TraceReconstructionError("no_trace_events")

    TraceReconstructor._validate_surfaces(events)

    ordered = TraceReconstructor._enforce_order(events)

    trace = {
        "trace_id": "REPLAY_TRACE",
        "epoch_id": registry.get("epoch", {}).get("current"),
        "request_hash": "REPLAY_RECONSTRUCTION",
        "events": ordered,
        "execution_trace_surface_set": sorted(surfaces),
    }

    trace["trace_root_hash"] = compute_trace_root(ordered)

    return trace


# ============================================================
# SUMMARY
# ============================================================

def summarize_trace(trace: Dict[str, Any]) -> ReconstructionSummary:

    events = trace["events"]

    surfaces = sorted({
        e.get("surface")
        for e in events
        if e.get("surface") is not None
    })

    return ReconstructionSummary(
        deterministic=True,
        replay_safe=True,
        event_count=len(events),
        trace_root_hash=trace["trace_root_hash"],
        execution_surface_set=surfaces,
    )
