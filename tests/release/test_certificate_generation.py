from __future__ import annotations

import json
from pathlib import Path
import subprocess


def test_certificate_generation_rejects_dirty_tree() -> None:
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
    (root / "tmp-release-governance-marker.txt").write_text("dirty", encoding="utf-8")
    try:
        subprocess.run(
            ["python3", "scripts/release/generate_certificate.py", "--product", "novaride", "--candidate", "NOVARIDE-RC-001"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        cert = json.loads((root / "artifacts" / "release-baseline" / "certificates" / "novaride" / "NOVARIDE-RC-001-CERT-001.json").read_text(encoding="utf-8"))
        assert cert["result"] == "REJECTED"
    finally:
        (root / "tmp-release-governance-marker.txt").unlink(missing_ok=True)
