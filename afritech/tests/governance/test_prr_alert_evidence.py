from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/operations/PRR_ALERT_EXERCISE_EVIDENCE.md"
REPORT = ROOT / "reports/prr/prr-alert-exercise.yaml"


def test_alert_exercise_evidence_exists() -> None:
    assert DOC.exists()
    assert REPORT.exists()

    text = DOC.read_text(encoding="utf-8")
    for item in (
        "ApiDown",
        "NginxDown",
        "DatabaseDown",
        "ContainerUnhealthy",
        "CertificateExpirySoon",
        "CpuHigh",
        "MemoryHigh",
        "DiskHigh",
        "ApiErrorRateHigh",
        "HighLatency",
    ):
        assert item in text

    payload = yaml.safe_load(REPORT.read_text(encoding="utf-8"))
    assert payload["evidence_type"] == "alert_exercise"
    assert len(payload["alerts"]) == 10
    assert all("pass_fail" in alert for alert in payload["alerts"])
