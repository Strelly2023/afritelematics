from __future__ import annotations

import json
from pathlib import Path
import subprocess


def test_evidence_manifest_validation_runs() -> None:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["python3", "scripts/release/validate_evidence_manifests.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads((root / "artifacts" / "release-baseline" / "evidence" / "MANIFEST_VALIDATION_RESULT.json").read_text(encoding="utf-8"))
    assert "result" in payload
