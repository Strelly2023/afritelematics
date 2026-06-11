from __future__ import annotations

import sys

from afritech.design.solid import validate_lsp


def validate() -> None:
    passing = validate_lsp(
        (
            {
                "child": "AutoFeeding",
                "parent_behaviors": ("schedule", "dispense"),
                "child_behaviors": ("schedule", "dispense", "measure"),
            },
        )
    )
    if passing["valid"] is not True:
        raise RuntimeError(f"behavior-preserving subtype rejected: {passing}")

    failing = validate_lsp(
        (
            {
                "child": "ManualFeeding",
                "parent_behaviors": ("schedule", "dispense"),
                "child_behaviors": ("schedule",),
            },
        )
    )
    if failing["valid"] is not False:
        raise RuntimeError("behavior-breaking subtype was admitted")


def main() -> int:
    try:
        validate()
        print("Afriprog LSP validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog LSP validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
