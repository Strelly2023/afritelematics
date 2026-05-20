"""Compressed witness proof validator."""

from __future__ import annotations

from afritech.ci.validator_groups import run_validator_modules

MODULES = (
    "afritech.ci.witness_validator",
    "afritech.ci.runtime_certificate_validator",
    "afritech.ci.full_witness_coverage_validator",
)


def validate() -> None:
    run_validator_modules(MODULES)


def main() -> int:
    validate()
    print("✅ witness proof validators passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
