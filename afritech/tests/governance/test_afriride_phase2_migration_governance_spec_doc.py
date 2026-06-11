from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/pilot/AFRIRIDE_PHASE2_MIGRATION_GOVERNANCE_SPEC.md"
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_phase2_spec_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "Status: PHASE 2 MIGRATION GOVERNANCE SPEC" in text
    assert "Classification: SQLITE_TO_POSTGRES_EQUIVALENCE_GATE" in text
    assert "This specification is not migration success evidence." in text

    for item in (
        "production readiness",
        "public pilot readiness",
        "real-world safety",
        "distributed fault tolerance",
        "high concurrency correctness",
    ):
        assert item in lowered


def test_phase2_spec_defines_equivalence_objective_and_prerequisites() -> None:
    text = read_doc()

    for item in (
        "migration must preserve replay, evidence, and receipt equivalence",
        "SQLite source remains the current authority before cutover",
        'replay diff must report "ok": true',
        "python3 -m afritech.guards.guard_phase1_runbook",
        "RULE-001-phase1-runbook.yaml",
        "AFRIRIDE_PHASE1_SETUP_RUNBOOK.md",
    ):
        assert item in text


def test_phase2_spec_references_governed_artifacts_and_gates() -> None:
    text = read_doc()

    for item in (
        "afriride_postgres_schema_v1.sql",
        "afriride_sqlite_to_postgres_migrate.py",
        "afriride_replay_diff_checker.py",
        "afriride_postgres_cutover_runbook.sh",
        "AFRIRIDE_POSTGRES_RUNTIME_VALIDATION_CHECKLIST.md",
        "AFRIRIDE_POSTGRES_CUTOVER_RUNBOOK.md",
        "Gate 1. Schema integrity",
        "Gate 2. Migration exit status",
        "Gate 3. Replay equivalence",
        "Gate 4. Runtime boot",
        "Gate 5. Restart stability",
    ):
        assert item in text


def test_phase2_spec_preserves_stop_conditions_and_claim_discipline() -> None:
    text = read_doc()

    for item in (
        "wrong source database selected",
        "wrong target database selected",
        "migration exits non-zero",
        "replay diff fails",
        "restart changes replay/evidence/receipt outputs",
        "SQLite-to-Postgres equivalence validated for the governed source set",
        "production validated",
        "pilot validated",
        "bounded migration claim",
    ):
        assert item in text
