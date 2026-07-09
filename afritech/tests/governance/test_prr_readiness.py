from __future__ import annotations

from pathlib import Path
import yaml


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/operations/PRR-001.md"
REPORT = ROOT / "reports/prr/prr-001.yaml"


def test_prr_report_and_document_exist() -> None:
    assert DOC.exists()
    assert REPORT.exists()

    doc = DOC.read_text(encoding="utf-8")
    for item in ("PRR-001 Production Readiness Review", "READY_FOR_PRR_APPROVAL", "GA allowed: false"):
        assert item in doc

    report = yaml.safe_load(REPORT.read_text(encoding="utf-8"))
    assert report["report_id"] == "PRR-001"
    assert report["status"] == "READY_FOR_PRR_APPROVAL"
    assert report["ga_allowed"] is False
    assert report["ga_approval"] == "PENDING"
    assert report["real_payments_enabled"] is False
    assert report["real_payment_approval"] == "PENDING"
    for domain in ("engineering", "operations", "observability", "security", "governance", "compliance", "commercial"):
        assert report["domains"][domain] == "PASS"
