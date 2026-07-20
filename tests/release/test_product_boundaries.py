from __future__ import annotations

import json
from pathlib import Path
import subprocess


def test_product_boundaries_validate() -> None:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        ["python3", "scripts/release/validate_product_boundaries.py"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(
        (root / "artifacts/release-baseline/preflight/product-boundary-validation.json").read_text(encoding="utf-8")
    )
    assert report["status"] == "PASS"
    assert report["summary"]["products"] == ["novaid", "novapay", "novaride"]
