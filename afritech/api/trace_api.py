from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from afritech.simulation.validation_receipt import stable_hash


# ============================================================
# TRACE ID VALIDATION (API-LEVEL GUARANTEE)
# ============================================================

def validate_trace_id(trace_id: str) -> None:
    """Validate trace_id before any filesystem or routing logic."""

    if not trace_id:
        raise ValueError("invalid trace_id")

    if trace_id in {"", ".", ".."}:
        raise ValueError("invalid trace_id")

    if "/" in trace_id or "\\" in trace_id:
        raise ValueError("invalid trace_id")


# ============================================================
# TRACE STORE
# ============================================================

class TraceStoreAPI:
    """Bounded API for pilot trace inspection.

    Constraints:
    - Read-only access (no mutation)
    - Deterministic output
    - Closed-world path enforcement
    """

    def __init__(self, trace_dir: Path | str = "traces") -> None:
        self.trace_dir = Path(trace_dir)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def list_traces(self) -> List[str]:
        """Return sorted list of trace filenames."""
        if not self.trace_dir.exists():
            return []

        return sorted(
            path.name
            for path in self.trace_dir.glob("*.json")
            if path.is_file()
        )

    def load_trace(self, trace_id: str) -> Dict[str, Any]:
        """Load a trace safely by ID."""
        trace_path = self._trace_path(trace_id)

        if not trace_path.exists():
            raise FileNotFoundError(trace_id)

        try:
            payload = json.loads(trace_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("invalid JSON trace payload") from exc

        if not isinstance(payload, dict):
            raise ValueError("trace must be a JSON object")

        return payload

    def inspect_replay_readiness(self, trace_id: str) -> Dict[str, Any]:
        """Validate minimal replay readiness without executing replay."""
        trace = self.load_trace(trace_id)

        required_sections = (
            "events",
            "normalized_events",
            "execution_states",
            "witnesses",
        )

        missing = [section for section in required_sections if section not in trace]

        computed_hash = stable_hash(
            {
                section: trace.get(section, ())
                for section in required_sections
            }
        )

        recorded_hash = trace.get("hash")

        return {
            "trace_id": trace_id,
            "status": "ready" if not missing else "incomplete",
            "missing": missing,
            "recorded_hash": recorded_hash,
            "computed_hash": computed_hash,
            "hash_matches": recorded_hash == computed_hash,
            "sections_present": [k for k in required_sections if k in trace],
        }

    # ---------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------

    def _trace_path(self, trace_id: str) -> Path:
        """Resolve safe filesystem path for trace."""

        # NOTE: still enforce safety here (defense in depth)
        validate_trace_id(trace_id)

        filename = trace_id if trace_id.endswith(".json") else f"{trace_id}.json"
        return self.trace_dir / filename


# ============================================================
# ROUTER BUILDER
# ============================================================

def build_trace_router(store: TraceStoreAPI | None = None) -> APIRouter:
    """Construct trace API router with bounded store."""

    trace_store = store or TraceStoreAPI()

    router = APIRouter(
        prefix="/v1",
        tags=["pilot-traces"],
    )

    # -----------------------------------------------------
    # ROUTES
    # -----------------------------------------------------

    @router.get("/traces")
    def list_traces() -> Dict[str, List[str]]:
        return {
            "traces": trace_store.list_traces(),
        }

    @router.get("/traces/{trace_id}")
    def get_trace(trace_id: str) -> Dict[str, Any]:
        try:
            # ✅ CRITICAL FIX — enforce validation BEFORE store call
            validate_trace_id(trace_id)

            return trace_store.load_trace(trace_id)

        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail="trace not found",
            ) from exc

        except ValueError as exc:
            # ✅ Ensures test expects 400
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

    @router.post("/traces/{trace_id}/replay")
    def replay_trace(trace_id: str) -> Dict[str, Any]:
        """Validate replay readiness (non-executing)."""
        try:
            # ✅ CRITICAL FIX — enforce validation BEFORE store call
            validate_trace_id(trace_id)

            return trace_store.inspect_replay_readiness(trace_id)

        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=404,
                detail="trace not found",
            ) from exc

        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

    return router