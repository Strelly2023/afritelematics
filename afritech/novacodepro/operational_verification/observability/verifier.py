from __future__ import annotations

from .models import ObservabilityProviderConfig, ObservabilityVerificationResult


def verify_observability(config: ObservabilityProviderConfig, observed_signals: set[str] | None = None, backend_confirmed: bool = False) -> ObservabilityVerificationResult:
    signals = observed_signals or set()
    missing = tuple(signal for signal in config.required_signals if signal not in signals)
    verified = bool(config.enabled and not missing and backend_confirmed)
    return ObservabilityVerificationResult(
        configured=config.enabled,
        executed=bool(signals),
        verified=verified,
        provider=config.provider,
        trace_ids=("trace-development-only",) if signals else (),
        missing_signals=missing,
        evidence_refs=("reports/novacodepro/operational-verification/observability/observability-verification.yaml",),
        backend_ingestion_confirmed=backend_confirmed,
    )
