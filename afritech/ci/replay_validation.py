"""
afritech.ci.replay_validation

Canonical replay validation gate for AfriTech CI.

Constitutional boundary:
- Replay is the source of truth.
- Replay divergence is ALWAYS a hard failure.
- No execution may be admitted without replay equivalence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from afritech.execution.worker.types import WorkerResult
# afritech.ci.distributed_replay_validator

class ReplayValidationError(RuntimeError):
    """Raised when replay validation fails."""


@dataclass(frozen=True)
class ReplayValidationReport:
    """
    Canonical replay validation outcome.
    """
    verified: bool
    checked_results: int
    failures: tuple[str, ...]

    def assert_verified(self) -> None:
        """
        Hard enforcement gate.
        """
        if not self.verified:
            raise ReplayValidationError(
                "Replay validation failed:\n" + "\n".join(self.failures)
            )


# ---------------------------------------------------------
# CORE VALIDATION
# ---------------------------------------------------------

def validate_replay(results: Iterable[WorkerResult]) -> ReplayValidationReport:
    """
    Validate deterministic replay equivalence across WorkerResults.

    HARD RULES:
    - All results must be WorkerResult
    - No missing results
    - No divergence allowed
    - Replay hash must match
    """

    failures: list[str] = []
    checked = 0

    results_list = list(results)

    # ---------------------------------------------------------
    # BASIC STRUCTURE CHECK
    # ---------------------------------------------------------

    if not results_list:
        failures.append("no worker results provided")
        return ReplayValidationReport(False, 0, tuple(failures))

    # ---------------------------------------------------------
    # TYPE ENFORCEMENT
    # ---------------------------------------------------------

    for idx, result in enumerate(results_list):
        if not isinstance(result, WorkerResult):
            failures.append(
                f"non-WorkerResult detected at index {idx}: {type(result)}"
            )

    if failures:
        return ReplayValidationReport(False, checked, tuple(failures))

    # ---------------------------------------------------------
    # DETERMINISTIC BASELINE
    # ---------------------------------------------------------

    baseline = results_list[0]
    checked += 1

    # ---------------------------------------------------------
    # STRICT EQUIVALENCE
    # ---------------------------------------------------------

    for idx, result in enumerate(results_list[1:], start=1):
        checked += 1

        # ✅ FAST HASH CHECK
        if result.replay_hash != baseline.replay_hash:
            failures.append(
                f"replay hash mismatch at index {idx}: "
                f"{result.replay_hash} != {baseline.replay_hash}"
            )
            continue

        # ✅ DEEP STRUCTURAL CHECK
        if not result.is_replay_equivalent(baseline):
            failures.append(
                f"non-equivalent replay result at index {idx}"
            )

    return ReplayValidationReport(
        verified=not failures,
        checked_results=checked,
        failures=tuple(failures),
    )


# ---------------------------------------------------------
# STRICT GATE (CI ENTRYPOINT)
# ---------------------------------------------------------

def require_replay_verified(results: Iterable[WorkerResult]) -> ReplayValidationReport:
    """
    Enforce replay validation.

    THIS IS THE HARD CONSTITUTIONAL GATE.
    """
    report = validate_replay(results)

    if not report.verified:
        raise ReplayValidationError(
            "Replay verification failed:\n" + "\n".join(report.failures)
        )

    return report
