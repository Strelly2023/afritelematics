"""Validate that structural registries are populated and complete."""

from __future__ import annotations

import sys

from afritech.ci.completion_utils import (
    STRUCTURAL_YAML,
    fail,
    load_yaml,
    main_result,
    require_no_empty_structural_artifacts,
)


def validate() -> None:
    require_no_empty_structural_artifacts()

    for path in STRUCTURAL_YAML:
        payload = load_yaml(path)
        if "schema" not in payload and "version" not in payload:
            fail(f"{path} must declare schema or version")
        if path.name != "SURFACE_STATUS.yaml" and "metadata" not in payload:
            if "authority" not in payload:
                fail(f"{path} must declare metadata or authority")

    print(f"✅ Structural artifacts validated: {len(STRUCTURAL_YAML)}")


def main() -> int:
    return main_result("Registry completeness validation", validate)


if __name__ == "__main__":
    sys.exit(main())
