"""Validate the bounded public proof surface."""

from __future__ import annotations

import subprocess
import sys

EXPECTED_LINES = (
    "=== AFRITECH CONTINUITY PROOF ===",
    "Continuity preserved under simulated disruption [OK]",
    "Replay equivalence maintained [OK]",
    "System integrity intact [OK]",
    "No claim is made for global deployment readiness",
)


def validate() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "afritech.demo.proof"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "proof surface failed")

    missing = [line for line in EXPECTED_LINES if line not in result.stdout]
    if missing:
        raise RuntimeError(f"proof surface missing expected lines: {missing}")


def main() -> int:
    validate()
    print("✅ proof surface validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
