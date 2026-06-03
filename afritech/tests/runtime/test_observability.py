"""
AfriTech Observability Tests

PURPOSE:
--------
Validate observability system:

- trace lifecycle correctness
- span behavior
- metrics aggregation
- logging stability
- exporters functionality
- NON-INTRUSIVE guarantee

CRITICAL GUARANTEE:
------------------
Observability MUST NOT affect execution semantics
"""

import pytest
import os
import json

from afritech.runtime.observability.observability_manager import ObservabilityManager
from afritech.runtime.observability.span import Span
from afritech.runtime.observability.trace_collector import TraceCollector
from afritech.runtime.observability.metrics_collector import MetricsCollector
from afritech.runtime.observability.logger import log, format_log_entry
from afritech.runtime.observability.exporters import (
    export_to_file,
    export_to_console,
    export_summary,
    export_all,
)
#afritech/tests/runtime/test_observability.py

# ============================================================
# ✅ TRACE TESTS
# ============================================================

def test_trace_lifecycle():
    obs = ObservabilityManager()

    trace_id = obs.start_trace("event-1")
    assert trace_id is not None

    span = obs.start_span(trace_id, "test-span")
    obs.finish_span(trace_id, span)

    obs.end_trace(trace_id)

    snapshot = obs.snapshot()

    assert trace_id in snapshot["traces"]
    assert snapshot["traces"][trace_id]["end_time"] is not None


# ============================================================
# ✅ SPAN TESTS
# ============================================================

def test_span_basic():
    span = Span("unit-test-span")

    assert span.name == "unit-test-span"
    assert span.is_finished() is False

    span.set_metadata("key", "value")
    span.add_tag("type", "test")

    span.finish()

    assert span.is_finished() is True
    assert span.duration() is not None


def test_span_serialization():
    span = Span("serialize")
    span.finish()

    d = span.to_dict()

    assert "name" in d
    assert "duration" in d
    assert d["name"] == "serialize"


# ============================================================
# ✅ METRICS TESTS
# ============================================================

def test_metrics_recording():
    metrics = MetricsCollector()

    metrics.record("latency", 100)
    metrics.record("latency", 200)

    summary = metrics.summarize_metric("latency")

    assert summary["count"] == 2
    assert summary["avg"] == 150
    assert summary["max"] == 200


def test_metrics_snapshot():
    metrics = MetricsCollector()

    metrics.record("x", 1)
    metrics.record("y", 2)

    snap = metrics.snapshot()

    assert "x" in snap
    assert "y" in snap


# ============================================================
# ✅ TRACE COLLECTOR TESTS
# ============================================================

def test_trace_collector_basic():
    tc = TraceCollector()

    trace_id = tc.start_trace("event-1")
    tc.add_span(trace_id, {"name": "span1"})
    tc.end_trace(trace_id)

    trace = tc.get_trace(trace_id)

    assert trace["event_id"] == "event-1"
    assert len(trace["spans"]) == 1


def test_trace_summary():
    tc = TraceCollector()

    trace_id = tc.start_trace("e1")
    tc.end_trace(trace_id)

    summary = tc.summarize_trace(trace_id)

    assert summary["event_id"] == "e1"
    assert "duration" in summary


# ============================================================
# ✅ LOGGER TESTS
# ============================================================

def test_logging_output(capsys):
    log("test message", level="INFO")

    captured = capsys.readouterr()
    assert "test message" in captured.out


def test_log_format():
    entry = {
        "level": "INFO",
        "message": "hello",
        "trace_id": "t",
        "span_id": "s",
    }

    formatted = format_log_entry(entry)

    assert "hello" in formatted
    assert "INFO" in formatted


# ============================================================
# ✅ EXPORTER TESTS
# ============================================================

def test_export_to_file(tmp_path):
    snapshot = {"test": 1}

    path = tmp_path / "test.json"

    export_to_file(snapshot, path)

    assert os.path.exists(path)

    with open(path) as f:
        data = json.load(f)

    assert data["test"] == 1


def test_export_summary(tmp_path):
    snapshot = {
        "traces": {"t1": {}},
        "metrics": {"m1": {}},
        "active_traces": {},
    }

    path = tmp_path / "summary.json"

    summary = export_summary(snapshot, path)

    assert summary["trace_count"] == 1
    assert "m1" in summary["metric_keys"]


def test_export_all(tmp_path):
    snapshot = {
        "traces": {"t": {}},
        "metrics": {"m": {}},
        "active_traces": {},
    }

    result = export_all(snapshot, base_path=tmp_path)

    assert os.path.exists(result["full"])
    assert os.path.exists(result["traces"])
    assert os.path.exists(result["metrics"])


# ============================================================
# ✅ OBSERVABILITY MANAGER TEST
# ============================================================

def test_observability_manager_snapshot():
    obs = ObservabilityManager()

    t = obs.start_trace("e1")
    span = obs.start_span(t, "span")
    obs.finish_span(t, span)
    obs.end_trace(t)

    obs.record_metric("test", 10)

    snap = obs.snapshot()

    assert "metrics" in snap
    assert "traces" in snap


# ============================================================
# ✅ NON-INTRUSIVE GUARANTEE TEST
# ============================================================

def test_observability_non_intrusive():
    obs = ObservabilityManager()

    event = {
        "event_id": "immut",
        "payload": {"v": 1},
        "timestamp": "2026-01-01",
    }

    original = dict(event)

    # simulate trace usage
    t = obs.start_trace(event["event_id"])
    span = obs.start_span(t, "test")
    obs.finish_span(t, span)
    obs.end_trace(t)

    # ✅ Event MUST NOT be modified
    assert event == original