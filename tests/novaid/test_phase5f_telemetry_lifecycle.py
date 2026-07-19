import json
from threading import enumerate as threads

from fastapi.testclient import TestClient

from afritech.novaid.observability import NovaIDMetrics, NovaIDTracer


def test_prometheus_export_is_low_cardinality() -> None:
    metrics = NovaIDMetrics()
    metrics.increment("novaid_authentication_attempts_total", outcome="success")
    metrics.increment("novaid_authentication_attempts_total", outcome="success")
    exported = metrics.prometheus()
    assert 'novaid_authentication_attempts_total{outcome="success"} 2' in exported
    assert "identity_id" not in exported
    assert "password" not in exported


def test_trace_file_export_is_structured_and_secret_free(tmp_path) -> None:
    target = tmp_path / "novaid-spans.jsonl"
    tracer = NovaIDTracer(export_path=target)
    with tracer.span("novaid.session.expire", {"operation": "session.expire"}):
        pass
    exported = json.loads(target.read_text().strip())
    assert exported == {
        "attributes": {"operation": "session.expire"},
        "error": None,
        "name": "novaid.session.expire",
    }
    assert "password" not in target.read_text()


def test_server_lifespan_readiness_metrics_and_shutdown() -> None:
    from afritech.novaid.server import app

    before = {thread.name for thread in threads()}
    with TestClient(app) as client:
        assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 200
        assert client.get("/metrics").status_code == 200
    after = {thread.name for thread in threads()}
    assert not ({"novaid-outbox-publisher", "novaid-revocation-consumer"} & (after - before))
