from __future__ import annotations

from pathlib import Path
import subprocess


def test_evidence_manifest_repair_runs() -> None:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["python3", "scripts/release/repair_evidence_manifests.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert (root / "artifacts" / "release-baseline" / "evidence" / "MANIFEST_REPAIR_LOG.json").exists()
