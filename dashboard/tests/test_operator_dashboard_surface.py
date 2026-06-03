from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_operator_dashboard_reads_required_ga_test_endpoints() -> None:
    source = read("src/App.jsx")

    assert 'readJson("/rides/active")' in source
    assert 'readJson("/system/replay/health")' in source
    assert 'readJson("/system/evidence")' in source
    assert 'readJson("/system/guards")' in source


def test_operator_dashboard_sends_test_instrumentation_headers() -> None:
    source = read("src/App.jsx")

    assert "TEST_MODE" in source
    assert "DEVICE_ID" in source
    assert '"X-AfriRide-Device-Id"' in source
    assert '"X-AfriRide-App-Version"' in source
    assert '"X-AfriRide-Event-Id"' in source
    assert '"X-AfriRide-Client-Timestamp"' in source


def test_operator_dashboard_is_read_only_surface() -> None:
    source = read("src/App.jsx")

    assert 'method: "POST"' not in source
    assert "override" not in source.lower()
    assert "certify" not in source.lower()
    assert "Replay & Evidence Control" in source
