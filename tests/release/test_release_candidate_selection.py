from __future__ import annotations

import json
from pathlib import Path
import subprocess


def test_release_candidate_selection_and_validation() -> None:
    root = Path(__file__).resolve().parents[2]
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    result = subprocess.run(
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
    assert "INITIAL-GA-AU-VIC-001-RC-SET-001" in result.stdout
    manifest = json.loads((root / "release/candidates/RELEASE_CANDIDATE_SET.json").read_text(encoding="utf-8"))
    assert manifest["products_share_commit"] is True
    validate = subprocess.run(
        ["python3", "scripts/release/validate_release_candidates.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert validate.returncode == 0, validate.stdout + validate.stderr
