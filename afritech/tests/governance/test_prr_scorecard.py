from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/operations/PRR_001_SCORECARD.md"
REPORT = ROOT / "reports/prr/prr-001-scorecard.yaml"


def test_prr_scorecard_exists_and_scores_are_maximum() -> None:
    assert DOC.exists()
    assert REPORT.exists()

    doc = DOC.read_text(encoding="utf-8")
    assert "overall: 10" in doc
    assert "observability: 10" in doc
    assert "PRR-001" in doc

    payload = yaml.safe_load(REPORT.read_text(encoding="utf-8"))
    for domain in (
        "engineering",
        "operations",
        "observability",
        "governance",
        "security",
        "compliance",
        "commercial",
    ):
        assert payload["domains"][domain] == 10
    assert payload["overall"] == 10
    assert payload["ga_allowed"] is False
