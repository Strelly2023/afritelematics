from ecosystems.afriride.core.infrastructure.observability.dispatch_metrics import (
    DispatchMetrics,
)


def test_metrics_tracking():

    metrics = DispatchMetrics()

    metrics.record_attempt("ride_001")
    metrics.record_attempt("ride_001")
    metrics.record_retry("ride_001")
    metrics.record_assignment("ride_001")

    assert metrics.get_attempts("ride_001") == 2
    assert metrics.get_retries("ride_001") == 1
    assert metrics.is_assigned("ride_001") is True