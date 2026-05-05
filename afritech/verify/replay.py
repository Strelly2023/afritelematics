from __future__ import annotations

"""
AfriTech Constitutional Replay Verifier
=======================================

CLI entrypoint for machine-checkable constitutional replay verification.

This verifier proves that the current AfriTech sovereign state is the
lawful result of its entire constitutional history.

IMPORTANT CONSTITUTIONAL GUARANTEES:
- Read-only
- Non-authoritative
- No runtime or guard coupling
- No mutation of registry, epochs, or audit logs
- Failure indicates UNLAWFUL HISTORY, not enforcement
"""

import sys

from afritech.verify.engine import verify_replay
from afritech.verify.report import print_report


def main() -> None:
    """
    Execute constitutional replay verification.

    Exit codes:
      0 -> Replay valid
      1 -> Replay invalid
    """
    print("🔁 AFRITECH CONSTITUTIONAL REPLAY")
    print("Loading epoch history...")
    print("Verifying epoch chain...")
    print("Verifying reseal continuity...")
    print("Verifying registry attestation...")
    print("Verifying invariant preservation...")
    print("Verifying ADR legitimacy...")

    result = verify_replay()

    print_report(result)

    if result.valid:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()