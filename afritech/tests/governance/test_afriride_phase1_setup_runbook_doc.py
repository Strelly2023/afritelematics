from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/pilot/AFRIRIDE_PHASE1_SETUP_RUNBOOK.md"
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_phase1_setup_runbook_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "Status: SETUP RUNBOOK" in text
    assert "Classification: OPERATOR AND ENGINEER EXECUTION SURFACE" in text
    assert "This runbook is not runtime authority." in text

    for item in (
        "determinism",
        "replay correctness",
        "receipt correctness",
        "production readiness",
        "pilot readiness",
        "real-world safety",
    ):
        assert item in lowered


def test_phase1_setup_runbook_defines_environment_and_dependency_setup() -> None:
    text = read_doc()

    for item in (
        "python3 -m venv .venv",
        "pip install -r requirements.txt",
        'import psycopg',
        'pip install "psycopg[binary]"',
        "afriride_system/tests/test_authentication.py",
        "afriride_system/tests/test_api_flow.py",
        "afriride_system/tests/test_persistence_durability.py",
    ):
        assert item in text


def test_phase1_setup_runbook_defines_dual_database_and_schema_validation() -> None:
    text = read_doc()

    for item in (
        "SQLite -> baseline and local reference",
        "Postgres -> target runtime",
        "AFRIRIDE_DB_PATH",
        "afriride_system/pilot_state.sqlite3",
        "AFRIRIDE_DATABASE_URL",
        "scripts/sql/afriride_postgres_schema_v1.sql",
        "trace_events",
        "idempotency_records",
        "replay_snapshots",
        "evidence_records",
        "receipt_records",
        "event_id",
        "sequence_id",
        "event_hash",
    ):
        assert item in text


def test_phase1_setup_runbook_matches_real_api_surface() -> None:
    text = read_doc()

    for item in (
        "uvicorn afriride_system.api.main:app --reload",
        "http://127.0.0.1:8000/health",
        "http://127.0.0.1:8000/docs",
        "http://127.0.0.1:8000/auth/token",
        "http://127.0.0.1:8000/passenger/request-ride",
        '"service": "afriride-api"',
        '"status": "success"',
        '"status": "REQUESTED"',
        '"error": null',
        "Idempotency-Key: setup-request-1",
    ):
        assert item in text


def test_phase1_setup_runbook_links_forward_to_validation_and_rollout() -> None:
    text = read_doc()

    for item in (
        "AFRIRIDE_POSTGRES_RUNTIME_VALIDATION_CHECKLIST.md",
        "AFRIRIDE_POSTGRES_CUTOVER_RUNBOOK.md",
        "AFRIRIDE_FIRST_PILOT_ROLLOUT_PLAN.md",
    ):
        assert item in text
