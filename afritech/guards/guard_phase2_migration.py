"""Guard the Phase 2 migration governance chain."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
BIND = ROOT / "afritech/governance/bindings/BIND-001-phase1-phase2.yaml"
PHASE2_SPEC = ROOT / "docs/pilot/AFRIRIDE_PHASE2_MIGRATION_GOVERNANCE_SPEC.md"
PHASE3_SPEC = ROOT / "docs/pilot/AFRIRIDE_PHASE3_LIVE_OPERATIONS_MONITORING_GOVERNANCE_SPEC.md"
CUTOVER_GATE = ROOT / "scripts/run_cutover_gate.sh"


class Phase2MigrationGuardError(RuntimeError):
    """Raised when the Phase 2 migration governance chain drifts."""


@dataclass(frozen=True)
class Phase2MigrationGuardReport:
    bind_id: str
    phase2_spec: str
    cutover_gate: str
    phase3_spec_present: bool
    required_gate_count: int

    @property
    def verified(self) -> bool:
        return (
            self.bind_id == "BIND-001"
            and self.phase2_spec == "docs/pilot/AFRIRIDE_PHASE2_MIGRATION_GOVERNANCE_SPEC.md"
            and self.cutover_gate == "scripts/run_cutover_gate.sh"
            and self.phase3_spec_present is True
            and self.required_gate_count == 5
        )


def validate() -> Phase2MigrationGuardReport:
    bind = _load_yaml(BIND)
    if bind.get("id") != "BIND-001":
        raise Phase2MigrationGuardError("BIND-001 id mismatch")

    for path in (
        PHASE2_SPEC,
        PHASE3_SPEC,
        CUTOVER_GATE,
        ROOT / "scripts/run_phase1_setup.sh",
        ROOT / "scripts/afriride_postgres_cutover_runbook.sh",
        ROOT / "scripts/afriride_sqlite_to_postgres_migrate.py",
        ROOT / "scripts/afriride_replay_diff_checker.py",
        ROOT / "scripts/sql/afriride_postgres_schema_v1.sql",
    ):
        if not path.exists():
            raise Phase2MigrationGuardError(f"missing governed artifact: {path}")

    phase2_text = PHASE2_SPEC.read_text(encoding="utf-8")
    phase3_text = PHASE3_SPEC.read_text(encoding="utf-8")
    cutover_text = CUTOVER_GATE.read_text(encoding="utf-8")
    cutover_runbook_text = (ROOT / "scripts/afriride_postgres_cutover_runbook.sh").read_text(
        encoding="utf-8"
    )

    bindings = bind.get("bindings")
    if not isinstance(bindings, list) or len(bindings) < 5:
        raise Phase2MigrationGuardError("BIND-001 must define five binding surfaces")

    linked_rules = tuple(bind.get("linked_rules", ()))
    for rule_id in ("RULE-001", "RULE-001-5"):
        if rule_id not in linked_rules:
            raise Phase2MigrationGuardError(f"BIND-001 missing linked rule: {rule_id}")

    for required in (
        "This specification is not migration success evidence.",
        "migration must preserve replay, evidence, and receipt equivalence",
        'replay diff must report "ok": true',
        "Gate 1. Schema integrity",
        "Gate 2. Migration exit status",
        "Gate 3. Replay equivalence",
        "Gate 4. Runtime boot",
        "Gate 5. Restart stability",
        "AFRIRIDE_PHASE1_SETUP_RUNBOOK.md",
        "RULE-001-phase1-runbook.yaml",
    ):
        if required not in phase2_text:
            raise Phase2MigrationGuardError(f"Phase 2 spec incomplete: {required}")

    for required in (
        "Status: PHASE 3 LIVE OPERATIONS AND MONITORING GOVERNANCE SPEC",
        "Classification: LIVE_OPERATIONS_REPLAY_LINKED_MONITORING_GATE",
        "This specification is not live production success evidence.",
        "observability explains trace-backed state",
        "observability never overrides trace-backed state",
        "replay divergence alert",
        "token/auth anomaly alert",
        "cutover gate completed",
    ):
        if required not in phase3_text:
            raise Phase2MigrationGuardError(f"Phase 3 spec incomplete: {required}")

    for required in (
        "python3 -m afritech.guards.guard_phase1_runbook",
        "python3 -m afritech.guards.guard_phase2_migration",
        "scripts/afriride_postgres_cutover_runbook.sh",
        "--skip-phase1",
        "--skip-guards",
        "GO: cutover gate passed",
        "NO-GO: cutover gate failed",
    ):
        if required not in cutover_text:
            raise Phase2MigrationGuardError(f"cutover gate missing: {required}")

    for required in (
        "afriride_sqlite_to_postgres_migrate.py",
        "afriride_replay_diff_checker.py",
        "AFRIRIDE_DATABASE_URL",
        "RIDER_TOKEN",
        "DRIVER_TOKEN",
        "OPERATOR_TOKEN",
    ):
        if required not in cutover_runbook_text:
            raise Phase2MigrationGuardError(f"cutover runbook script drifted: {required}")

    execution_flow = bind.get("execution_flow")
    if not isinstance(execution_flow, list) or len(execution_flow) != 5:
        raise Phase2MigrationGuardError("BIND-001 execution flow must contain five steps")

    report = Phase2MigrationGuardReport(
        bind_id=str(bind["id"]),
        phase2_spec="docs/pilot/AFRIRIDE_PHASE2_MIGRATION_GOVERNANCE_SPEC.md",
        cutover_gate="scripts/run_cutover_gate.sh",
        phase3_spec_present=True,
        required_gate_count=5,
    )
    if not report.verified:
        raise Phase2MigrationGuardError("Phase 2 migration guard report failed")
    return report


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Phase2MigrationGuardError(f"{path} must contain a mapping")
    return payload


def main() -> int:
    report = validate()
    print(
        "PHASE2_MIGRATION_GUARD: PASS "
        f"(bind={report.bind_id}, cutover_gate={report.cutover_gate}, phase3_spec={report.phase3_spec_present})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
