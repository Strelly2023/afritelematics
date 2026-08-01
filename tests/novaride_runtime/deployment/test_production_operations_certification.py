from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def test_production_operations_certification_is_fail_closed(tmp_path: Path) -> None:
    output = tmp_path / "certification.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/novaride/certify_production_operations.py",
            "--output",
            str(output),
        ],
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    payload = json.loads(output.read_text())
    assert payload["final_status"] == "BLOCKED"
    assert payload["checks"]["ha_topology"]["status"] == "PASS"
    assert payload["checks"]["live_backup_restore"]["status"] == "BLOCKED"
    assert payload["checks"]["live_dr_rto_rpo"]["status"] == "BLOCKED"


def test_backup_refuses_unencrypted_production_execution(tmp_path: Path) -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "NOVARIDE_POSTGRES_DSN": "postgresql://example.invalid/database",
            "NOVARIDE_BACKUP_DIR": str(tmp_path),
            "NOVARIDE_ENVIRONMENT": "production",
        }
    )
    environment.pop("NOVARIDE_BACKUP_AGE_RECIPIENT", None)

    result = subprocess.run(
        ["bash", "scripts/novaride/backup_runtime.sh"],
        env=environment,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "BACKUP_AGE_RECIPIENT" in result.stderr


def test_restore_refuses_source_database_as_target(tmp_path: Path) -> None:
    backup = tmp_path / "backup.dump"
    backup.write_bytes(b"not-used")
    dsn = "postgresql://example.invalid/database"
    environment = os.environ.copy()
    environment.update(
        {
            "NOVARIDE_POSTGRES_DSN": dsn,
            "NOVARIDE_RESTORE_TARGET_DSN": dsn,
            "NOVARIDE_ALLOW_ISOLATED_RESTORE": "1",
        }
    )

    result = subprocess.run(
        ["bash", "scripts/novaride/restore_runtime.sh", str(backup)],
        env=environment,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "must not equal" in result.stderr
