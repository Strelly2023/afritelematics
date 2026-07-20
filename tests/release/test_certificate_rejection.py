from __future__ import annotations

import json
from pathlib import Path
import subprocess


def test_certificate_audit_runs() -> None:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["python3", "scripts/release/audit_existing_certificates.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    audit = json.loads((root / "artifacts" / "release-baseline" / "certificates" / "CERTIFICATE_AUDIT.json").read_text(encoding="utf-8"))
    assert "certificates" in audit
