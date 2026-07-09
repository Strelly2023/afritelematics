from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/operations/PRR_LIVE_HEALTH_EVIDENCE.md"
REPORT = ROOT / "reports/prr/prr-live-health.yaml"


def test_live_health_evidence_exists_and_is_structured() -> None:
    assert DOC.exists()
    assert REPORT.exists()

    text = DOC.read_text(encoding="utf-8")
    for item in (
        "api.afritechnology.com/health",
        "api.afritechnology.com/live",
        "api.afritechnology.com/ready",
        "identity.afritechnology.com/healthz",
        "trust.afritechnology.com/healthz",
        "merchant.afritechnology.com/healthz",
        "developer.afritechnology.com/healthz",
    ):
        assert item in text

    payload = yaml.safe_load(REPORT.read_text(encoding="utf-8"))
    assert payload["evidence_type"] == "live_health"
    assert payload["ga_allowed"] is False
    assert payload["real_payments_enabled"] is False
    assert len(payload["checks"]) >= 7
