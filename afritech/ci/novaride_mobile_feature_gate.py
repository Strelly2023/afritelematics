"""Fail-closed NovaRide Rider/Driver/Operator functional release gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MATRICES = (
    ROOT / "requirements/novaride/mobile-feature-traceability.yaml",
    ROOT / "requirements/novaride/driver-feature-traceability.yaml",
)
ALLOWED_STATES = {
    "NOT_IMPLEMENTED",
    "PARTIALLY_IMPLEMENTED",
    "IMPLEMENTED",
    "TESTED",
    "VERIFIED",
    "BLOCKED",
    "BLOCKED_EXTERNAL",
    "FAILED",
}
PASS_STATES = {"VERIFIED"}
COMMON_FIELDS = {
    "id",
    "title",
    "application",
    "journey",
    "screen",
    "component",
    "source_file",
    "api_endpoint",
    "event",
    "backend_service",
    "database_entity",
    "novaid_policy",
    "novapay_transaction",
    "authorization_rule",
    "unit_test",
    "integration_test",
    "mobile_e2e_test",
    "cross_application_e2e_test",
    "build_artifact",
    "evidence_file",
    "release_commit",
    "state",
}
MANDATORY_GATES = (
    "RIDER_FEATURE_COMPLETENESS",
    "DRIVER_FEATURE_COMPLETENESS",
    "OPERATOR_FEATURE_COMPLETENESS",
    "RIDER_DRIVER_OPERATOR_E2E",
    "DRIVER_ELIGIBILITY_GATE",
    "VEHICLE_INSPECTION_GATE",
    "DRIVER_SHIFT_LIFECYCLE",
    "DRIVER_DISPATCH_WORKFLOW",
    "RIDER_VERIFICATION_WORKFLOW",
    "TRIP_LIFECYCLE_SYNCHRONIZATION",
    "NOVAID_DRIVER_INTEGRATION",
    "NOVAPAY_RIDER_PAYMENT",
    "NOVAPAY_DRIVER_EARNINGS",
    "DRIVER_SAFETY_WORKFLOW",
    "RIDER_SAFETY_WORKFLOW",
    "OPERATOR_SAFETY_WORKFLOW",
    "INCIDENT_MANAGEMENT",
    "DRIVER_OFFLINE_RECOVERY",
    "ACCESSIBILITY_VALIDATION",
    "LOCALIZATION_VALIDATION",
    "PRODUCTION_MOCK_SCAN",
    "TESTED_BINARY_EQUALS_RELEASE_BINARY",
)


@dataclass(frozen=True)
class GateReport:
    decision: str
    tested_commit: str
    matrices: list[str]
    requirement_count: int
    state_counts: dict[str, int]
    gates: dict[str, str]
    errors: list[str]
    generated_at: str

    @property
    def passed(self) -> bool:
        return self.decision == "GO"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _head_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _load_requirements(paths: tuple[Path, ...]) -> tuple[list[dict[str, Any]], list[str]]:
    requirements: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if not path.is_file():
            errors.append(f"missing traceability matrix: {path}")
            continue
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        items = payload.get("requirements") if isinstance(payload, dict) else None
        if not isinstance(items, list) or not items:
            errors.append(f"{path}: requirements must be a non-empty list")
            continue
        for index, item in enumerate(items):
            label = f"{path.name}:requirements[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label} must be a mapping")
                continue
            missing = sorted(COMMON_FIELDS - set(item))
            if missing:
                errors.append(f"{label} missing fields: {', '.join(missing)}")
            requirement_id = item.get("id")
            if not isinstance(requirement_id, str) or not requirement_id:
                errors.append(f"{label} has invalid id")
            elif requirement_id in seen:
                errors.append(f"duplicate requirement id: {requirement_id}")
            else:
                seen.add(requirement_id)
            state = item.get("state")
            if state not in ALLOWED_STATES:
                errors.append(f"{requirement_id or label} has invalid state: {state}")
            for field in COMMON_FIELDS - {"release_commit"}:
                if field in item and field != "state" and (
                    not isinstance(item[field], str) or not item[field].strip()
                ):
                    errors.append(f"{requirement_id or label} requires {field}")
            if state == "VERIFIED":
                for field in (
                    "source_file",
                    "unit_test",
                    "integration_test",
                    "mobile_e2e_test",
                    "cross_application_e2e_test",
                    "build_artifact",
                    "evidence_file",
                    "release_commit",
                ):
                    value = item.get(field)
                    if not isinstance(value, str) or not value.strip():
                        errors.append(f"{requirement_id} VERIFIED requires {field}")
                    elif field in {
                        "source_file",
                        "unit_test",
                        "integration_test",
                        "mobile_e2e_test",
                        "cross_application_e2e_test",
                        "build_artifact",
                        "evidence_file",
                    } and not (ROOT / value).is_file():
                        errors.append(f"{requirement_id} VERIFIED has missing {field}: {value}")
            requirements.append(item)
    return requirements, errors


def evaluate(
    paths: tuple[Path, ...] = DEFAULT_MATRICES,
    *,
    certification: Path | None = None,
    tested_binary: Path | None = None,
    release_binary: Path | None = None,
) -> GateReport:
    requirements, errors = _load_requirements(paths)
    commit = _head_commit()
    counts = {state: 0 for state in sorted(ALLOWED_STATES)}
    for item in requirements:
        state = item.get("state")
        if state in counts:
            counts[state] += 1

    applications = {"rider", "driver", "operator"}
    gates = {gate: "FAIL" for gate in MANDATORY_GATES}
    for application in applications:
        app_items = [r for r in requirements if r.get("application") == application]
        gate = f"{application.upper()}_FEATURE_COMPLETENESS"
        if app_items and all(r.get("state") in PASS_STATES for r in app_items):
            gates[gate] = "PASS"

    if tested_binary and release_binary:
        if tested_binary.is_file() and release_binary.is_file():
            if _sha256(tested_binary) == _sha256(release_binary):
                gates["TESTED_BINARY_EQUALS_RELEASE_BINARY"] = "PASS"
        else:
            errors.append("tested and release binaries must both exist")

    if certification:
        if not certification.is_file():
            errors.append(f"missing certification: {certification}")
        else:
            payload = json.loads(certification.read_text(encoding="utf-8"))
            if payload.get("tested_commit") != commit:
                errors.append("certification tested_commit does not match HEAD")
            supplied = payload.get("gates", {})
            for gate in MANDATORY_GATES:
                if supplied.get(gate) == "PASS":
                    gates[gate] = "PASS"

    # Completeness can never be supplied by an untrusted summary when the
    # underlying requirement records are not independently VERIFIED.
    for application in applications:
        gate = f"{application.upper()}_FEATURE_COMPLETENESS"
        app_items = [r for r in requirements if r.get("application") == application]
        if not app_items or any(r.get("state") != "VERIFIED" for r in app_items):
            gates[gate] = "FAIL"

    decision = "GO" if not errors and all(v == "PASS" for v in gates.values()) else "NO_GO"
    return GateReport(
        decision=decision,
        tested_commit=commit,
        matrices=[_display_path(path) for path in paths],
        requirement_count=len(requirements),
        state_counts={key: value for key, value in counts.items() if value},
        gates=gates,
        errors=errors,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


def write_report(report: GateReport, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({**asdict(report), "passed": report.passed}, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", action="append", type=Path)
    parser.add_argument("--certification", type=Path)
    parser.add_argument("--tested-binary", type=Path)
    parser.add_argument("--release-binary", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    paths = tuple(args.matrix) if args.matrix else DEFAULT_MATRICES
    report = evaluate(
        paths,
        certification=args.certification,
        tested_binary=args.tested_binary,
        release_binary=args.release_binary,
    )
    if args.output:
        write_report(report, args.output)
    print(json.dumps({**asdict(report), "passed": report.passed}, indent=2, sort_keys=True))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
