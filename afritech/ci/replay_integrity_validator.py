"""Compressed replay integrity validator."""

from __future__ import annotations

from afritech.ci.validator_groups import run_validator_modules
from afritech.verify.engine import verify_replay

MODULES = (
    "afritech.ci.trace_reconstruction_validator",
)


def validate() -> None:
    result = verify_replay()
    if not result.valid:
        raise RuntimeError("; ".join(result.violations))
    run_validator_modules(MODULES)


def main() -> int:
    validate()
    print("✅ replay integrity validators passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
