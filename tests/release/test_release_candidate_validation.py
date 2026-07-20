from __future__ import annotations

import json
from pathlib import Path
import subprocess


def test_release_candidate_validation_reports_pass() -> None:
    root = Path(__file__).resolve().parents[2]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    subprocess.run(
        [
            "python3",
            "scripts/release/select_release_candidates.py",
            "--novatech-scope",
            "release/scopes/INITIAL_GA_SCOPE.yaml",
            "--novaid-commit",
            commit,
            "--novaride-commit",
            commit,
            "--novapay-commit",
            commit,
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        ["python3", "scripts/release/validate_release_candidates.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((root / "artifacts" / "release-baseline" / "preflight" / "release-candidate-validation.json").read_text(encoding="utf-8"))
    assert report["status"] == "PASS"
