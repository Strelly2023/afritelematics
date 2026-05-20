"""Compressed execution integrity validator."""

from __future__ import annotations

from afritech.ci.validator_groups import run_validator_modules

MODULES = (
    "afritech.ci.ast_call_order_validator",
    "afritech.ci.ast_import_validator",
    "afritech.ci.execution_completeness_validator",
)


def validate() -> None:
    run_validator_modules(MODULES)


def main() -> int:
    validate()
    print("✅ execution integrity validators passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
