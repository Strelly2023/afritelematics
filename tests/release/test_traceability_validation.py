from __future__ import annotations

import subprocess
from pathlib import Path


def test_traceability_generation_and_validation() -> None:
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
    subprocess.run(
        ["python3", "scripts/release/generate_traceability_reports.py"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    validate = subprocess.run(
        ["python3", "scripts/release/validate_traceability.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert validate.returncode == 0, validate.stdout + validate.stderr
