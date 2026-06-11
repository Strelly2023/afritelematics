from __future__ import annotations

import sys

from afritech.runtime_monitoring import collect_runtime_events

VALIDATOR_NAME = "afritech.ci.afriprog_runtime_non_authority_validator"


def validate() -> None:
    events = collect_runtime_events(errors=("boom",))
    for key in (
        "activation_allowed",
        "runtime_mutation_allowed",
        "rollback_execution_allowed",
    ):
        if events[key] is not False:
            raise RuntimeError(f"runtime monitoring gained authority: {key}")


def main() -> int:
    try:
        validate()
        print("Afriprog runtime non-authority validation PASSED")
        return 0
    except Exception as exc:
        print(f"Afriprog runtime non-authority validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
