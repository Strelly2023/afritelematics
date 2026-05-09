# afritech/trace/trace_engine.py

"""
AfriTech Trace Engine

Builds canonical, deterministic execution traces.

Responsibilities:
- construct ordered trace events
- maintain causal dependencies (chain + DAG)
- compute event hashes
- compute trace root commitment
- enforce trace invariants
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional

from afritech.trace.trace_context import TraceContext
from afritech.trace.trace_hash import (
    compute_event_hash,
    compute_trace_root,
    validate_trace,
    TraceHashError,
    hash_obj,
)


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class TraceEngineError(Exception):
    """Trace construction or validation error"""
    pass


# -----------------------------------------------------------------
# ENGINE
# -----------------------------------------------------------------

class TraceEngine:
    """
    Deterministic trace construction engine.

    One instance = one execution trace.
    """

    # =============================================================
    # INIT
    # =============================================================

    def __init__(self):
        self.context: Optional[TraceContext] = None
        self.trace: Optional[Dict[str, Any]] = None
        self._finalized: bool = False

    # =============================================================
    # TRACE START
    # =============================================================

    def start(self, ctx: TraceContext) -> None:
        """
        Start a new trace.

        Must be called exactly once.
        """

        if self.context is not None:
            raise TraceEngineError("trace_already_started")

        if not ctx.trace_id or not ctx.epoch_id or not ctx.request_hash:
            raise TraceEngineError("invalid_trace_context")

        self.context = ctx

        self.trace = {
            "trace_id": ctx.trace_id,
            "epoch_id": ctx.epoch_id,
            "request_hash": ctx.request_hash,
            "events": [],
        }

    # =============================================================
    # RECORD EVENT (BEGIN)
    # =============================================================

    def record(
        self,
        step: str,
        payload: Dict[str, Any],
        *,
        depends_on: Optional[List[int]] = None,
        authority_context_hash: Optional[str] = None,
    ) -> int:
        """
        Record the start of a trace event.

        Returns:
            event index
        """

        if self._finalized:
            raise TraceEngineError("trace_already_finalized")

        if self.trace is None:
            raise TraceEngineError("trace_not_started")

        if not step:
            raise TraceEngineError("missing_step")

        idx = len(self.trace["events"])

        # ---------------------------------------------------------
        # PARENT CHAIN (LINEAR ORDER)
        # ---------------------------------------------------------

        parent_event_hash = (
            self.trace["events"][-1]["event_hash"]
            if idx > 0
            else "GENESIS"
        )

        # ---------------------------------------------------------
        # DEPENDENCIES (DAG)
        # ---------------------------------------------------------

        deps = depends_on or []

        for dep in deps:
            if not isinstance(dep, int) or dep < 0 or dep >= idx:
                raise TraceEngineError("invalid_dependency_reference")

        # ---------------------------------------------------------
        # AUTHORITY CONTEXT
        # ---------------------------------------------------------

        authority_context_hash = (
            authority_context_hash
            or self._derive_authority_context_hash()
        )

        # ---------------------------------------------------------
        # BUILD OPEN EVENT
        # ---------------------------------------------------------

        event: Dict[str, Any] = {
            "index": idx,
            "step": step,
            "parent_event_hash": parent_event_hash,
            "depends_on": sorted(deps),
            "authority_context_hash": authority_context_hash,
            "payload": payload,
            "status": "OPEN",
        }

        self.trace["events"].append(event)
        return idx

    # =============================================================
    # COMPLETE EVENT (END)
    # =============================================================

    def complete(
        self,
        step: str,
        result: Dict[str, Any],
    ) -> None:
        """
        Complete the most recent OPEN event.
        """

        if self._finalized:
            raise TraceEngineError("trace_already_finalized")

        if self.trace is None or not self.trace["events"]:
            raise TraceEngineError("no_event_to_complete")

        event = self.trace["events"][-1]

        if event["status"] != "OPEN":
            raise TraceEngineError("event_already_completed")

        if event["step"] != step:
            raise TraceEngineError("step_mismatch")

        # ---------------------------------------------------------
        # FINALIZE EVENT
        # ---------------------------------------------------------

        event["result"] = result
        event["status"] = "CLOSED"

        # ---------------------------------------------------------
        # HASH EVENT
        # ---------------------------------------------------------

        event["event_hash"] = compute_event_hash(event)

    # =============================================================
    # AUTHORITY CONTEXT HASH
    # =============================================================

    def _derive_authority_context_hash(self) -> str:
        """
        Deterministic authority binding for this trace.
        """

        if self.context is None:
            raise TraceEngineError("trace_not_started")

        base = {
            "epoch_id": self.context.epoch_id,
            "request_hash": self.context.request_hash,
        }

        return hash_obj(base)

    # =============================================================
    # FINALIZE TRACE
    # =============================================================

    def finalize(self) -> str:
        """
        Finalize trace and return trace root hash.
        """

        if self._finalized:
            raise TraceEngineError("trace_already_finalized")

        if self.trace is None:
            raise TraceEngineError("trace_not_started")

        if not self.trace["events"]:
            raise TraceEngineError("empty_trace_not_allowed")

        # ---------------------------------------------------------
        # ENSURE ALL EVENTS CLOSED
        # ---------------------------------------------------------

        for event in self.trace["events"]:
            if event.get("status") != "CLOSED":
                raise TraceEngineError("open_event_remaining")

        # ---------------------------------------------------------
        # COMPUTE TRACE ROOT
        # ---------------------------------------------------------

        self.trace["trace_root_hash"] = compute_trace_root(
            self.trace["events"]
        )

        # ---------------------------------------------------------
        # VALIDATE TRACE STRUCTURE
        # ---------------------------------------------------------

        try:
            validate_trace(self.trace)
        except TraceHashError as e:
            raise TraceEngineError(
                f"trace_validation_failed: {e}"
            )

        self._finalized = True
        return self.trace["trace_root_hash"]

    # =============================================================
    # EXPORT
    # =============================================================

    def to_dict(self) -> Dict[str, Any]:
        if self.trace is None:
            raise TraceEngineError("trace_not_started")
        return self.trace

    # =============================================================
    # SAFE BUILD (IDEMPOTENT)
    # =============================================================

    def build(self) -> Dict[str, Any]:
        """
        Finalize trace if needed and return it.
        """
        if not self._finalized:
            self.finalize()
        return self.trace

    # =============================================================
    # INLINE VERIFY (REPLAY USE)
    # =============================================================

    def verify(self) -> bool:
        if self.trace is None:
            return False
        try:
            validate_trace(self.trace)
            return True
        except Exception:
            return False

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
        return (
            f"<TraceEngine events={len(self.trace['events']) if self.trace else 0} "
            f"finalized={self._finalized}>"
        )
