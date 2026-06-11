"""Validate timeline playback as a replay viewer only."""

from __future__ import annotations

import sys

from afritech.afriprogramming.tooling_surfaces import (
    build_timeline_playback,
    explain_replay_step,
)
from afritech.ci.afriprogramming_tooling_surface_common import (
    fail,
    validate_tooling_behavior,
)


VALIDATOR_NAME = "afritech.ci.timeline_playback_viewer_validator"


def validate_timeline_playback_viewer() -> None:
    def behavior() -> None:
        timeline = build_timeline_playback(
            (
                {
                    "id": "e1",
                    "timestamp": "2026-06-01T00:00:00Z",
                    "status": "valid",
                },
            )
        )
        if timeline["viewer_only"] is not True:
            fail("timeline playback must remain viewer only")
        if timeline["playback_defines_truth"] is not False:
            fail("timeline playback must not define truth")
        explanation = explain_replay_step(timeline["steps"][0])
        if explanation["explanation_authority"] != "advisory":
            fail("timeline explanations must remain advisory")
        if explanation["validators_remain_final"] is not True:
            fail("timeline explanations must preserve validator authority")

    validate_tooling_behavior("timeline_playback_viewer", VALIDATOR_NAME, behavior)


def main() -> int:
    try:
        validate_timeline_playback_viewer()
        print("Timeline playback viewer validation PASSED")
        return 0
    except Exception as exc:
        print(f"Timeline playback viewer validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
