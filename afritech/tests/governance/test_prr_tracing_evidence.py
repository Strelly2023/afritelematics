from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/operations/PRR_TRACING_EVIDENCE.md"
REPORT = ROOT / "reports/prr/prr-tracing-evidence.yaml"


def test_tracing_evidence_exists_and_mentions_correlation_headers() -> None:
    assert DOC.exists()
    assert REPORT.exists()

    text = DOC.read_text(encoding="utf-8")
    for item in (
        "request_id",
        "trace_id",
        "span_id",
        "traceparent",
        "X-Request-ID",
        "X-Trace-Id",
        "X-Span-Id",
        "OpenTelemetry collector",
    ):
        assert item in text

    payload = yaml.safe_load(REPORT.read_text(encoding="utf-8"))
    assert payload["evidence_type"] == "tracing"
    assert payload["trace_pipeline"]["traces"] is True
    assert payload["trace_pipeline"]["metrics"] is True
    assert payload["headers"]["X-Request-ID"] is True
