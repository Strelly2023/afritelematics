# afritech/trace/trace_validator.py

"""
AfriTech Trace Validator

Purpose:
Validate trace correctness under full constitutional invariants.

Guarantees:
- index contiguity
- parent chain integrity
- dependency graph validity (DAG)
- event hash correctness
- trace root correctness
- deterministic replay safety

This is the enforcement layer for TRACE (Phase A).
"""

from __future__ import annotations

from typing import Dict, Any, List, Set

from afritech.trace.trace_hash import (
    compute_event_hash,
    compute_trace_root,
    canonical_json,
    TraceHashError,
)


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class TraceValidationError(Exception):
    """Raised when trace violates invariants"""
    pass


# -----------------------------------------------------------------
# VALIDATOR (AUTHORITATIVE)
# -----------------------------------------------------------------

class TraceValidator:

    # =============================================================
    # ENTRYPOINT
    # =============================================================

    @classmethod
    def validate(cls, trace: Dict[str, Any]) -> bool:
        cls._validate_structure(trace)

        events = trace["events"]

        cls._validate_index_contiguity(events)
        cls._validate_event_hashes(events)
        cls._validate_parent_chain(events)
        cls._validate_dependencies(events)
        cls._validate_acyclic(events)

        cls._validate_root(trace, events)
        cls._validate_header(trace)
        cls._validate_determinism(trace)

        return True

    # =============================================================
    # STRUCTURE
    # =============================================================

    @staticmethod
    def _validate_structure(trace: Dict[str, Any]):

        required_fields = [
            "trace_id",
            "request_hash",
            "epoch_id",
            "events",
        ]

        for field in required_fields:
            if field not in trace:
                raise TraceValidationError(f"missing_field: {field}")

        if not isinstance(trace["events"], list):
            raise TraceValidationError("events_not_list")

        if len(trace["events"]) == 0:
            raise TraceValidationError("empty_trace")

    # =============================================================
    # INDEX CONTIGUITY (I16_1)
    # =============================================================

    @staticmethod
    def _validate_index_contiguity(events: List[Dict[str, Any]]):

        for i, e in enumerate(events):
            if e.get("index") != i:
                raise TraceValidationError("index_contiguity_violation")

    # =============================================================
    # EVENT HASH VALIDATION (I16_5)
    # =============================================================

    @staticmethod
    def _validate_event_hashes(events: List[Dict[str, Any]]):

        for e in events:
            if "event_hash" not in e:
                raise TraceValidationError("missing_event_hash")

            expected = compute_event_hash(e)

            if e["event_hash"] != expected:
                raise TraceValidationError("event_hash_invalid")

    # =============================================================
    # PARENT CHAIN VALIDATION (I16_2)
    # =============================================================

    @staticmethod
    def _validate_parent_chain(events: List[Dict[str, Any]]):

        for i, e in enumerate(events):

            expected_parent = (
                "GENESIS" if i == 0 else events[i - 1]["event_hash"]
            )

            if e.get("parent_event_hash") != expected_parent:
                raise TraceValidationError("parent_chain_invalid")

    # =============================================================
    # DEPENDENCY VALIDATION (I16_3)
    # =============================================================

    @staticmethod
    def _validate_dependencies(events: List[Dict[str, Any]]):

        for e in events:

            idx = e["index"]
            deps = e.get("depends_on", [])

            if not isinstance(deps, list):
                raise TraceValidationError("depends_on_not_list")

            for d in deps:

                if not isinstance(d, int):
                    raise TraceValidationError("dependency_not_int")

                if d < 0:
                    raise TraceValidationError("negative_dependency")

                if d >= idx:
                    raise TraceValidationError("forward_dependency_violation")

    # =============================================================
    # DAG ACYCLIC VALIDATION (I16_4)
    # =============================================================

    @staticmethod
    def _validate_acyclic(events: List[Dict[str, Any]]):

        visited: Set[int] = set()
        stack: Set[int] = set()

        def visit(i: int):
            if i in stack:
                raise TraceValidationError("cycle_detected")

            if i in visited:
                return

            stack.add(i)

            for dep in events[i].get("depends_on", []):
                visit(dep)

            stack.remove(i)
            visited.add(i)

        for i in range(len(events)):
            visit(i)

    # =============================================================
    # ROOT VALIDATION (I16_6)
    # =============================================================

    @staticmethod
    def _validate_root(trace: Dict[str, Any], events):

        try:
            expected_root = compute_trace_root(events)
        except TraceHashError as e:
            raise TraceValidationError(f"root_hash_error: {e}")

        actual_root = trace.get("trace_root_hash")

        if actual_root != expected_root:
            raise TraceValidationError("trace_root_invalid")

    # =============================================================
    # HEADER VALIDATION
    # =============================================================

    @staticmethod
    def _validate_header(trace: Dict[str, Any]):

        if not isinstance(trace.get("trace_id"), str):
            raise TraceValidationError("invalid_trace_id")

        if not isinstance(trace.get("request_hash"), str):
            raise TraceValidationError("invalid_request_hash")

        if not isinstance(trace.get("epoch_id"), str):
            raise TraceValidationError("invalid_epoch_id")

    # =============================================================
    # DETERMINISM (I16_7 + I16_10)
    # =============================================================

    @staticmethod
    def _validate_determinism(trace: Dict[str, Any]):

        try:
            canonical_json(trace)
        except Exception:
            raise TraceValidationError("non_deterministic_structure")

    # =============================================================
    # SAFE VALIDATION
    # =============================================================

    @classmethod
    def try_validate(cls, trace: Dict[str, Any]) -> bool:
        try:
            return cls.validate(trace)
        except TraceValidationError:
            return False


# -----------------------------------------------------------------
# FUNCTION EXPORT (CRITICAL FIX FOR YOUR ERROR)
# -----------------------------------------------------------------

def validate_trace(trace: Dict[str, Any]) -> bool:
    """
    Public functional entrypoint (required by replay, engine, reconstructor)
    """
    return TraceValidator.validate(trace)