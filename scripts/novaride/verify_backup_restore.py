#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "reports" / "novaride" / "deployment" / "backup-restore-certification.yaml"


def main() -> int:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        yaml.safe_dump(
            {
                "status": "PENDING",
                "postgres_backup": "not_executed_no_live_dsn",
                "event_store_backup": "not_executed_no_live_dsn",
                "projection_backup": "not_executed_no_live_dsn",
                "restore_to_isolated_environment": "not_executed",
                "replay_after_restore": "not_executed",
                "external_side_effects_blocked": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
