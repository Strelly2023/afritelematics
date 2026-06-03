"""Validate deterministic load proof profiles for production readiness."""

from __future__ import annotations

from afritech.load.proof import (
    DEFAULT_LOAD_PROFILES,
    LoadProofError,
    LoadProofReport,
    run_required_load_proofs,
)


class LoadProofValidationError(RuntimeError):
    """Raised when load proof validation fails."""


def validate() -> LoadProofReport:
    try:
        report = run_required_load_proofs(DEFAULT_LOAD_PROFILES)
    except LoadProofError as exc:
        raise LoadProofValidationError(str(exc)) from exc

    _validate_report(report)
    return report


def _validate_report(report: LoadProofReport) -> None:
    counts = tuple(profile.event_count for profile in report.profiles)
    if counts != DEFAULT_LOAD_PROFILES:
        raise LoadProofValidationError(
            f"load profiles mismatch: expected {DEFAULT_LOAD_PROFILES}, got {counts}"
        )
    for profile in report.profiles:
        if not profile.replay_hash_stable:
            raise LoadProofValidationError(
                f"replay hash drift at {profile.event_count} events"
            )
        if not profile.partition_order_stable:
            raise LoadProofValidationError(
                f"partition order drift at {profile.event_count} events"
            )
        if not profile.worker_result_stable:
            raise LoadProofValidationError(
                f"worker result drift at {profile.event_count} events"
            )
        if not profile.hidden_mutation_absent:
            raise LoadProofValidationError(
                f"hidden mutation detected at {profile.event_count} events"
            )


def main() -> int:
    try:
        report = validate()
    except LoadProofValidationError as exc:
        print(f"Load proof validation FAILED: {exc}")
        return 1

    for profile in report.profiles:
        print(
            "Load proof profile PASSED: "
            f"{profile.event_count} events "
            f"replay_hash={profile.first_run.replay_hash}"
        )
    print(f"Load proof validation PASSED: report_hash={report.report_hash()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
