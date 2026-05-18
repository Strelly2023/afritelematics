"""Ensure active surfaces are either IMPLEMENTED or FROZEN."""

from __future__ import annotations

import sys

from afritech.ci.completion_utils import (
    active_entries,
    main_result,
    validate_entry_state_resolution,
)


def validate() -> None:
    validate_entry_state_resolution()
    print(f"✅ Active surface resolutions checked: {len(active_entries())}")


def main() -> int:
    return main_result("Surface state resolution validation", validate)


if __name__ == "__main__":
    sys.exit(main())
