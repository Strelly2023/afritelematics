"""Validate replay graph viewer as visualization only."""

from __future__ import annotations

import sys

from afritech.afriprogramming.tooling_surfaces import build_replay_graph
from afritech.ci.afriprogramming_tooling_surface_common import (
    fail,
    validate_tooling_behavior,
)


VALIDATOR_NAME = "afritech.ci.replay_graph_viewer_validator"


def validate_replay_graph_viewer() -> None:
    def behavior() -> None:
        graph = build_replay_graph(
            (
                {"id": "e1", "event_type": "RideRequested", "status": "valid"},
                {"id": "e2", "event_type": "RideAccepted", "status": "valid"},
            )
        )
        if graph["viewer_only"] is not True:
            fail("replay graph must remain viewer only")
        if graph["replay_required_for_truth"] is not True:
            fail("replay graph must require replay for truth")
        if len(graph["nodes"]) != 2 or len(graph["edges"]) != 1:
            fail("replay graph viewer emitted invalid graph shape")

    validate_tooling_behavior("replay_graph_viewer", VALIDATOR_NAME, behavior)


def main() -> int:
    try:
        validate_replay_graph_viewer()
        print("Replay graph viewer validation PASSED")
        return 0
    except Exception as exc:
        print(f"Replay graph viewer validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
