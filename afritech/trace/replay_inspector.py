from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Protocol


class ReplayEngine(Protocol):
    def execute(self, normalized_events: Sequence[dict[str, Any]]) -> Sequence[dict[str, Any]]:
        """Replay normalized events into execution states."""


class ReplayInspector:
    """Inspect pilot traces by replaying normalized events."""

    def replay(self, trace: dict[str, Any], engine: ReplayEngine) -> tuple[dict[str, Any], ...]:
        replayed = tuple(dict(state) for state in engine.execute(trace["normalized_events"]))
        expected = tuple(dict(state) for state in trace["execution_states"])
        if replayed != expected:
            raise AssertionError("Replay mismatch")
        return replayed


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python3 -m afritech.trace.replay_inspector <trace.json>")
        return 2

    trace_path = Path(sys.argv[1])
    trace = json.loads(trace_path.read_text(encoding="utf-8"))
    print(
        json.dumps(
            {
                "trace_id": trace.get("trace_id"),
                "hash": trace.get("hash"),
                "normalized_event_count": len(trace.get("normalized_events", ())),
                "execution_state_count": len(trace.get("execution_states", ())),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
