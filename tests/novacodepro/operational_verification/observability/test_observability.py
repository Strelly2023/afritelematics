from afritech.novacodepro.operational_verification.observability import ObservabilityProviderConfig, verify_observability


def test_configured_collector_is_not_automatically_verified() -> None:
    result = verify_observability(ObservabilityProviderConfig("opentelemetry", True), set(), False)

    assert result.configured is True
    assert result.executed is False
    assert result.verified is False


def test_backend_ingestion_confirmation_required() -> None:
    signals = {"traces", "metrics", "logs", "errors", "performance"}

    pending = verify_observability(ObservabilityProviderConfig("opentelemetry", True), signals, False)
    verified = verify_observability(ObservabilityProviderConfig("opentelemetry", True), signals, True)

    assert pending.verified is False
    assert verified.verified is True


def test_missing_metrics_or_logs_fail_when_required() -> None:
    result = verify_observability(ObservabilityProviderConfig("azure_monitor", True), {"traces", "errors"}, True)

    assert "metrics" in result.missing_signals
    assert "logs" in result.missing_signals
    assert result.verified is False
