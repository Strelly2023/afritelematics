from __future__ import annotations

import json
import subprocess
from pathlib import Path


def test_migration_schema_and_live_verification_scripts_emit_reports() -> None:
    subprocess.run(["python3", "scripts/novaride/verify_runtime_migrations.py"], check=True)
    subprocess.run(["python3", "scripts/novaride/verify_event_schema_compatibility.py"], check=True)
    subprocess.run(["python3", "scripts/novaride/verify_live_runtime.py"], check=True)
    subprocess.run(["python3", "scripts/novaride/verify_backup_restore.py"], check=True)

    migration = json.loads(
        Path("reports/novaride/deployment/runtime-migration-verification.json").read_text()
    )
    schema = json.loads(
        Path("reports/novaride/deployment/event-schema-compatibility.json").read_text()
    )
    live = Path("reports/novaride/deployment/live-runtime-verification.yaml").read_text()

    assert migration["status"] == "PASS"
    assert migration["live_postgres_applied"] is False
    assert schema["status"] == "PASS"
    assert "CERTIFICATION_INCOMPLETE" in live
