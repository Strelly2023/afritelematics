"""Validate declared execution coverage is implemented or frozen."""

from __future__ import annotations

import sys

from afritech.ci.completion_utils import (
    RESOLVED_STATES,
    ROOT,
    UNRESOLVED_STATES,
    fail,
    load_yaml,
    main_result,
)


MATRIX = ROOT / "afritech/ci/execution_completion_matrix.yaml"


def validate() -> None:
    payload = load_yaml(MATRIX)
    surfaces = payload.get("surfaces")
    if not isinstance(surfaces, dict) or not surfaces:
        fail("execution completion matrix must declare surfaces")

    for name, entry in surfaces.items():
        if not isinstance(entry, dict):
            fail(f"surface {name} must be a mapping")
        state = entry.get("implementation_state")
        if state in UNRESOLVED_STATES:
            fail(f"surface {name} is unresolved: {state}")
        if state not in RESOLVED_STATES:
            fail(f"surface {name} has invalid state: {state}")
        if state == "IMPLEMENTED":
            tests = entry.get("tests")
            if not isinstance(tests, list) or not tests:
                fail(f"implemented surface {name} lacks test evidence")
            for test_path in tests:
                path = ROOT / test_path
                if not path.exists():
                    fail(f"surface {name} references missing test: {test_path}")
        if state == "FROZEN" and not entry.get("freeze_reason"):
            fail(f"frozen surface {name} lacks freeze_reason")

    print(f"✅ Execution coverage surfaces resolved: {len(surfaces)}")


def main() -> int:
    return main_result("Execution completeness validation", validate)


if __name__ == "__main__":
    sys.exit(main())
