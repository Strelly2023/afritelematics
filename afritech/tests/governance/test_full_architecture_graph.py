from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/architecture/AFRITECH_FULL_ARCHITECTURE_GRAPH.md"


def test_full_architecture_graph_generator_writes_expected_sections():
    result = subprocess.run(
        [sys.executable, "scripts/generate_architecture_graph.py"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert DOC.exists()

    text = DOC.read_text(encoding="utf-8")
    for needle in (
        "# AfriTech Full Architecture Graph",
        "## Runtime Architecture Graph",
        "```mermaid",
        "## Repository Architecture Inventory",
        "## Startup Inventory",
        "## Direct Startup Imports",
    ):
        assert needle in text
