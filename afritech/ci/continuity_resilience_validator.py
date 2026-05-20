"""Compressed continuity and resilience validator."""

from __future__ import annotations

from afritech.ci.validator_groups import run_validator_modules

MODULES = (
    "afritech.ci.continuity_validator",
    "afritech.ci.adversarial_runner_validator",
    "afritech.ci.afriride_continuity_demo_validator",
)


def validate() -> None:
    run_validator_modules(MODULES)


def run() -> None:
    validate()


def main() -> int:
    validate()
    print("✅ continuity resilience validators passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
