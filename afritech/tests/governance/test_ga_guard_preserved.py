from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "reports/prr/prr-001.yaml"


def test_ga_guard_is_preserved_in_prr_report() -> None:
    payload = yaml.safe_load(REPORT.read_text(encoding="utf-8"))
    assert payload["status"] == "READY_FOR_PRR_APPROVAL"
    assert payload["ga_allowed"] is False
    assert payload["ga_approval"] == "PENDING"
    assert payload["real_payments_enabled"] is False
    assert payload["real_payment_approval"] == "PENDING"
