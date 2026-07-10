from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_no_stale_hosts_script_passes() -> None:
    subprocess.run(
        ["python3", "scripts/mobile/assert_no_stale_api_hosts.py"],
        cwd=ROOT,
        check=True,
    )

