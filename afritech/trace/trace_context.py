# afritech/trace/trace_context.py

"""
Trace Context

Purpose:
Carry execution‑wide, immutable identifiers required for
deterministic trace construction, replay verification,
and registry binding.

Design principles:
- immutable (frozen)
- explicitly passed (never global)
- minimal but sufficient
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TraceContext:
    """
    Immutable execution‑scope trace context.

    Fields:
        trace_id:
            Unique identifier for this execution trace.

        epoch_id:
            Epoch under which execution occurs.
            Must match registry / replay epoch.

        request_hash:
            Deterministic hash of the external request or
            execution intent.

        root_event_id:
            Optional identifier of the root trace event.
            Filled by TraceEngine.start().
    """

    trace_id: str
    epoch_id: str
    request_hash: str
    root_event_id: Optional[str] = None
