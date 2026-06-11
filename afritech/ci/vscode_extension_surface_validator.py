"""Validate VSCode extension surface as UI only."""

from __future__ import annotations

import sys

from afritech.afriprogramming.tooling_surfaces import build_vscode_view_model
from afritech.ci.afriprogramming_tooling_surface_common import (
    fail,
    validate_tooling_behavior,
)


VALIDATOR_NAME = "afritech.ci.vscode_extension_surface_validator"


def validate_vscode_extension_surface() -> None:
    def behavior() -> None:
        view = build_vscode_view_model()
        if view["ui_only"] is not True:
            fail("VSCode extension must remain UI only")
        if view["defines_truth"] is not False:
            fail("VSCode extension must not define truth")
        if view["mutates_protected_runtime_state"] is not False:
            fail("VSCode extension must not mutate protected runtime state")

    validate_tooling_behavior("vscode_extension", VALIDATOR_NAME, behavior)


def main() -> int:
    try:
        validate_vscode_extension_surface()
        print("VSCode extension surface validation PASSED")
        return 0
    except Exception as exc:
        print(f"VSCode extension surface validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
