"""Compressed structural closure validator."""

from __future__ import annotations

from afritech.ci.validator_groups import run_validator_modules

MODULES = (
    "afritech.ci.yaml_gap_validator",
    "afritech.ci.registry_completeness_validator",
    "afritech.ci.surface_state_resolution_validator",
    "afritech.ci.completeness_policy_validator",
)


def validate() -> None:
    run_validator_modules(MODULES)


def main() -> int:
    validate()
    print("✅ structural closure validators passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
