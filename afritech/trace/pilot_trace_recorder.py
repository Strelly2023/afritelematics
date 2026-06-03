from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from afritech.simulation.validation_receipt import stable_hash


class PilotTraceRecorder:
    """Write canonical pilot traces for later replay inspection."""

    def __init__(self, trace_dir: Path | str = "traces") -> None:
        self.trace_dir = Path(trace_dir)

    def record(self, trace: dict[str, Any]) -> dict[str, Any]:
        trace_id = str(trace["trace_id"])
        canonical_trace = deepcopy(dict(trace))
        canonical_trace["hash"] = stable_hash(
            {
                "events": canonical_trace.get("events", ()),
                "execution_states": canonical_trace.get("execution_states", ()),
                "normalized_events": canonical_trace.get("normalized_events", ()),
                "witnesses": canonical_trace.get("witnesses", ()),
            }
        )

        self.trace_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.trace_dir / f"{trace_id}.json"
        output_path.write_text(
            json.dumps(canonical_trace, sort_keys=True, indent=2),
            encoding="utf-8",
        )
        return canonical_trace

    def load(self, trace_id: str) -> dict[str, Any]:
        payload = json.loads((self.trace_dir / f"{trace_id}.json").read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("pilot trace must be a mapping")
        return payload
