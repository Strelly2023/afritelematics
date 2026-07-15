from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ObservabilityProviderConfig:
    provider: str
    enabled: bool
    endpoint_env: str = ""
    required_signals: tuple[str, ...] = ("traces", "metrics", "logs", "errors", "performance")


@dataclass(frozen=True, slots=True)
class ObservabilityVerificationResult:
    configured: bool
    executed: bool
    verified: bool
    provider: str
    trace_ids: tuple[str, ...] = ()
    missing_signals: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    backend_ingestion_confirmed: bool = False
    metadata: dict[str, object] = field(default_factory=dict)
