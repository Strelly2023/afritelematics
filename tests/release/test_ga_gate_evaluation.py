from __future__ import annotations

import json
from pathlib import Path
import subprocess


def test_ga_gate_evaluation_produces_results() -> None:
    root = Path(__file__).resolve().parents[2]
    subprocess.run(
        ["python3", "scripts/release/evaluate_ga_gates.py"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    for product in ("NOVAID", "NOVARIDE", "NOVAPAY"):
        path = root / "artifacts" / "release-baseline" / "gates" / f"{product}_GATE_RESULT.json"
        assert path.exists()
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "classification" in data
