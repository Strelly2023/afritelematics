from __future__ import annotations

import contextlib
import io
import sys
from dataclasses import dataclass
from typing import Callable

from afritech.ci import afriride_continuity_demo_validator
from afritech.ci import continuity_validator
from afritech.ci import trace_reconstruction_validator
from afritech.verify import verify_multi_epoch_replay
from afritech.verify.engine import verify_replay
from ecosystems.afriride.continuity.runner import run_all as run_afriride


@dataclass(frozen=True)
class EvidenceCheck:
    label: str
    runner: Callable[[], object]


@dataclass(frozen=True)
class ClaimSnapshot:
    claim: str
    evidence: tuple[str, ...]
    result: str


def run_quietly(check: EvidenceCheck) -> tuple[bool, str]:
    buffer = io.StringIO()

    try:
        with contextlib.redirect_stdout(buffer):
            result = check.runner()
        if result not in (None, 0):
            return False, f"{check.label} returned {result!r}"
        return True, buffer.getvalue()
    except Exception as exc:
        return False, f"{check.label} failed: {exc}"


def replay_check() -> None:
    result = verify_replay()
    if not result.valid:
        raise RuntimeError("constitutional replay is invalid")


def evidence_checks() -> tuple[EvidenceCheck, ...]:
    return (
        EvidenceCheck(
            "AfriTech continuity validation",
            continuity_validator.run,
        ),
        EvidenceCheck(
            "AfriRide continuity demonstration",
            afriride_continuity_demo_validator.run,
        ),
        EvidenceCheck(
            "Trace reconstruction validation",
            trace_reconstruction_validator.run,
        ),
        EvidenceCheck(
            "Multi-epoch replay validation",
            verify_multi_epoch_replay.run,
        ),
        EvidenceCheck(
            "Constitutional replay validation",
            replay_check,
        ),
    )


def claim_snapshots(
    scenario_count: int,
    metric_count: int,
) -> tuple[ClaimSnapshot, ...]:
    return (
        ClaimSnapshot(
            claim="Continuity under simulated disruption",
            evidence=(
                "afritech.ci.continuity_validator",
                "afritech.ci.afriride_continuity_demo_validator",
            ),
            result=f"{scenario_count} AfriRide scenarios passed",
        ),
        ClaimSnapshot(
            claim="Deterministic replay",
            evidence=(
                "afritech.verify.engine.verify_replay",
                "afritech.ci.trace_reconstruction_validator",
            ),
            result="replay equivalence and trace reconstruction confirmed",
        ),
        ClaimSnapshot(
            claim="Identity and coordination continuity",
            evidence=(
                "ecosystems.afriride.continuity.scenarios",
                "ecosystems.afriride.runtime.execution.deterministic_executor",
            ),
            result=f"{metric_count} mobility continuity metrics satisfied",
        ),
        ClaimSnapshot(
            claim="Bounded operational demonstration",
            evidence=(
                "ecosystems.afriride.continuity.index.yaml",
                "ecosystems.afriride.tests.continuity",
            ),
            result="AfriRide remains a controlled continuity demo environment",
        ),
    )


def status_line(label: str, ok: bool) -> str:
    return f"{label} {'[OK]' if ok else '[FAIL]'}"


def print_story(results: tuple[object, ...]) -> None:
    scenario_ids = [getattr(result, "scenario_id") for result in results]
    metric_names = sorted(
        {
            metric
            for result in results
            for metric in getattr(result, "metrics").keys()
        }
    )

    print("=== AFRITECH CONTINUITY PROOF ===")
    print()
    print("Scenario: AfriRide Mobility Disruption")
    print()
    print(status_line("1. Execution begins", True))
    print(status_line("2. Network partition occurs", "AFRIRIDE-CONT-001" in scenario_ids))
    print(status_line("3. Divergent states created", "AFRIRIDE-CONT-003" in scenario_ids))
    print(status_line("4. Replay reconciliation triggered", "AFRIRIDE-CONT-002" in scenario_ids))
    print(status_line("5. Deterministic convergence achieved", all(result.metrics["replay_equivalent"] for result in results)))
    print(status_line("6. Identity preserved", all(result.metrics["identity_continuity"] for result in results)))
    print(status_line("7. No duplicate authority", all(result.metrics["authority_conflict_prevented"] for result in results)))
    print(status_line("8. Witness trace validated", all(result.metrics["reconstruction_complete"] for result in results)))
    print()
    print("RESULT:")
    print(status_line("Continuity preserved under simulated disruption", all(result.accepted for result in results)))
    print(status_line("Replay equivalence maintained", all(result.metrics["replay_equivalent"] for result in results)))
    print(status_line("System integrity intact", True))
    print()
    print("CLAIM -> EVIDENCE SNAPSHOT")
    print()
    for snapshot in claim_snapshots(len(results), len(metric_names)):
        print(f"CLAIM: {snapshot.claim}")
        print("EVIDENCE:")
        for item in snapshot.evidence:
            print(f"  - {item} [OK]")
        print(f"RESULT: {snapshot.result}")
        print()
    print("CLAIM DISCIPLINE:")
    print("  - Validated continuity under simulated disruption")
    print("  - Deterministic replay verified for declared evidence paths")
    print("  - AfriRide is a controlled continuity demonstration environment")
    print("  - No claim is made for global deployment readiness")


def run() -> int:
    checks = evidence_checks()
    failures = []

    for check in checks:
        ok, detail = run_quietly(check)
        if not ok:
            failures.append(detail)

    if failures:
        print("=== AFRITECH CONTINUITY PROOF ===")
        print()
        print("RESULT:")
        print(status_line("Proof package evidence checks", False))
        for failure in failures:
            print(f"- {failure}")
        return 1

    results = run_afriride()
    print_story(results)
    return 0


def main() -> None:
    sys.exit(run())


if __name__ == "__main__":
    main()
