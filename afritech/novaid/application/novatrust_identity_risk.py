"""Tenant-scoped NovaTrust identity-risk inputs for NovaID authorization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
from typing import Any, Callable


class NovaTrustIdentityRiskError(RuntimeError):
    pass


class NovaTrustOutcome(StrEnum):
    ALLOW = "ALLOW"
    CHALLENGE = "CHALLENGE"
    DENY = "DENY"
    BLOCK = "BLOCK"


class NovaTrustReason(StrEnum):
    ACCEPTABLE_RISK = "ACCEPTABLE_RISK"
    AUTHENTICATION_RISK = "AUTHENTICATION_RISK"
    DEVICE_UNTRUSTED = "DEVICE_UNTRUSTED"
    DEVICE_INVALID = "DEVICE_INVALID"
    IDENTITY_COMPROMISED = "IDENTITY_COMPROMISED"
    SANCTIONS_BLOCK = "SANCTIONS_BLOCK"
    RISK_BLOCK = "RISK_BLOCK"
    AUTHORITY_UNAVAILABLE = "AUTHORITY_UNAVAILABLE"
    INVALID_DECISION = "INVALID_DECISION"
    STALE_DECISION = "STALE_DECISION"
    CROSS_TENANT_MISMATCH = "CROSS_TENANT_MISMATCH"


class DeviceTrustResult(StrEnum):
    TRUSTED = "TRUSTED"
    UNVERIFIED = "UNVERIFIED"
    REVOKED = "REVOKED"
    INTEGRITY_FAILED = "INTEGRITY_FAILED"


class ScreeningResult(StrEnum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    CLEAR = "CLEAR"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class NovaTrustIdentityRiskRequest:
    tenant_id: str
    organization_id: str
    subject_id: str
    session_id: str
    provider_id: str
    authentication_strength: str
    correlation_id: str
    request_id: str
    evaluated_at: datetime
    device_id: str | None = None

    def __post_init__(self) -> None:
        required = (
            self.tenant_id, self.organization_id, self.subject_id,
            self.session_id, self.authentication_strength,
            self.correlation_id, self.request_id,
        )
        if not all(isinstance(value, str) and value.strip() for value in required):
            raise NovaTrustIdentityRiskError("NOVATRUST_REQUEST_INVALID")
        if self.evaluated_at.tzinfo is None:
            raise NovaTrustIdentityRiskError("NOVATRUST_REQUEST_TIME_INVALID")


@dataclass(frozen=True, slots=True)
class NovaTrustIdentityRiskSignals:
    tenant_id: str
    subject_id: str
    authentication_risk: Decimal
    device_trust: DeviceTrustResult
    identity_compromised: bool
    screening: ScreeningResult
    provenance: str

    def __post_init__(self) -> None:
        if not self.tenant_id or not self.subject_id or not self.provenance:
            raise NovaTrustIdentityRiskError("NOVATRUST_SIGNALS_INVALID")
        if not Decimal("0") <= self.authentication_risk <= Decimal("1"):
            raise NovaTrustIdentityRiskError("NOVATRUST_RISK_INVALID")


@dataclass(frozen=True, slots=True)
class NovaTrustIdentityRiskDecision:
    decision_id: str
    tenant_id: str
    subject_id: str
    outcome: NovaTrustOutcome
    reasons: tuple[NovaTrustReason, ...]
    risk_score: Decimal
    device_trust: DeviceTrustResult
    screening: ScreeningResult
    authority: str
    provenance: str
    correlation_id: str
    request_id: str
    evaluated_at: datetime
    expires_at: datetime

    @property
    def device_trusted(self) -> bool:
        return self.device_trust is DeviceTrustResult.TRUSTED

    def assert_consumable(self, request: NovaTrustIdentityRiskRequest, *, now: datetime) -> None:
        if self.tenant_id != request.tenant_id or self.subject_id != request.subject_id:
            raise NovaTrustIdentityRiskError(NovaTrustReason.CROSS_TENANT_MISMATCH)
        if self.request_id != request.request_id or self.correlation_id != request.correlation_id:
            raise NovaTrustIdentityRiskError(NovaTrustReason.INVALID_DECISION)
        if now.tzinfo is None or now < self.evaluated_at or now >= self.expires_at:
            raise NovaTrustIdentityRiskError(NovaTrustReason.STALE_DECISION)
        if not self.authority or not self.provenance:
            raise NovaTrustIdentityRiskError(NovaTrustReason.INVALID_DECISION)


class NovaTrustIdentityRiskAuthority:
    """Evaluates trust inputs; canonical NovaID policy remains authorization authority."""

    AUTHORITY = "NOVATRUST_IDENTITY_RISK_V1"

    def __init__(
        self, *, signal_resolver: Callable[[NovaTrustIdentityRiskRequest], NovaTrustIdentityRiskSignals],
        security_events: Any, freshness_seconds: int = 300,
    ) -> None:
        if not callable(signal_resolver) or freshness_seconds <= 0:
            raise NovaTrustIdentityRiskError("NOVATRUST_CONFIGURATION_INVALID")
        if security_events is None or not callable(getattr(security_events, "record", None)):
            raise NovaTrustIdentityRiskError("NOVATRUST_SECURITY_EVENT_REQUIRED")
        self._resolve = signal_resolver
        self._events = security_events
        self._freshness = freshness_seconds
        self._completed: dict[str, NovaTrustIdentityRiskDecision] = {}

    def evaluate(self, request: NovaTrustIdentityRiskRequest) -> NovaTrustIdentityRiskDecision:
        identity = "|".join((request.tenant_id, request.subject_id, request.request_id, self.AUTHORITY))
        decision_id = "ntr_" + sha256(identity.encode()).hexdigest()[:32]
        completed = self._completed.get(decision_id)
        if completed is not None:
            completed.assert_consumable(request, now=request.evaluated_at)
            return completed
        try:
            signals = self._resolve(request)
        except Exception as exc:
            self._record(request, NovaTrustOutcome.DENY, (NovaTrustReason.AUTHORITY_UNAVAILABLE,))
            raise NovaTrustIdentityRiskError(NovaTrustReason.AUTHORITY_UNAVAILABLE) from exc
        if not isinstance(signals, NovaTrustIdentityRiskSignals):
            self._record(request, NovaTrustOutcome.DENY, (NovaTrustReason.INVALID_DECISION,))
            raise NovaTrustIdentityRiskError(NovaTrustReason.INVALID_DECISION)
        if signals.tenant_id != request.tenant_id or signals.subject_id != request.subject_id:
            self._record(request, NovaTrustOutcome.DENY, (NovaTrustReason.CROSS_TENANT_MISMATCH,))
            raise NovaTrustIdentityRiskError(NovaTrustReason.CROSS_TENANT_MISMATCH)

        reasons: list[NovaTrustReason] = []
        outcome = NovaTrustOutcome.ALLOW
        if signals.identity_compromised:
            outcome, reasons = NovaTrustOutcome.BLOCK, [NovaTrustReason.IDENTITY_COMPROMISED]
        elif signals.screening is ScreeningResult.BLOCKED:
            outcome, reasons = NovaTrustOutcome.BLOCK, [NovaTrustReason.SANCTIONS_BLOCK]
        elif signals.screening in (
            ScreeningResult.NOT_CONFIGURED,
            ScreeningResult.UNAVAILABLE,
        ):
            outcome, reasons = (
                NovaTrustOutcome.DENY,
                [NovaTrustReason.AUTHORITY_UNAVAILABLE],
            )
        elif signals.authentication_risk >= Decimal("0.9"):
            outcome, reasons = NovaTrustOutcome.BLOCK, [NovaTrustReason.RISK_BLOCK]
        elif signals.authentication_risk >= Decimal("0.6"):
            outcome, reasons = NovaTrustOutcome.CHALLENGE, [NovaTrustReason.AUTHENTICATION_RISK]
        elif signals.device_trust in (DeviceTrustResult.REVOKED, DeviceTrustResult.INTEGRITY_FAILED):
            outcome, reasons = NovaTrustOutcome.DENY, [NovaTrustReason.DEVICE_INVALID]
        else:
            reasons = [NovaTrustReason.ACCEPTABLE_RISK]

        evaluated = request.evaluated_at.astimezone(UTC)
        decision = NovaTrustIdentityRiskDecision(
            decision_id=decision_id,
            tenant_id=request.tenant_id, subject_id=request.subject_id,
            outcome=outcome, reasons=tuple(reasons), risk_score=signals.authentication_risk,
            device_trust=signals.device_trust, screening=signals.screening,
            authority=self.AUTHORITY, provenance=signals.provenance,
            correlation_id=request.correlation_id, request_id=request.request_id,
            evaluated_at=evaluated, expires_at=evaluated + timedelta(seconds=self._freshness),
        )
        self._record(request, outcome, tuple(reasons), decision_id=decision.decision_id)
        self._completed[decision_id] = decision
        return decision

    def _record(self, request, outcome, reasons, *, decision_id: str = "") -> None:
        self._events.record(
            event_type="NOVATRUST_IDENTITY_RISK_DECISION", tenant_id=request.tenant_id,
            actor_type="WORKFORCE", actor_id=request.subject_id,
            subject_type="IDENTITY", subject_id=request.subject_id,
            outcome=outcome.value, correlation_id=request.correlation_id,
            request_id=request.request_id, reason_codes=tuple(reason.value for reason in reasons),
            session_id=request.session_id, source="novatrust_identity_risk",
            metadata={"decision_id": decision_id, "authority": self.AUTHORITY},
        )


def runtime_identity_risk_signals(request: NovaTrustIdentityRiskRequest) -> NovaTrustIdentityRiskSignals:
    """Conservative signals from verified runtime context; no external CLEAR is fabricated."""
    return NovaTrustIdentityRiskSignals(
        tenant_id=request.tenant_id, subject_id=request.subject_id,
        authentication_risk=Decimal("0"),
        device_trust=(DeviceTrustResult.TRUSTED if request.device_id else DeviceTrustResult.UNVERIFIED),
        identity_compromised=False, screening=ScreeningResult.NOT_CONFIGURED,
        provenance="verified_novaid_session_context",
    )


__all__ = [name for name in globals() if name.startswith("NovaTrust") or name in {"DeviceTrustResult", "ScreeningResult", "runtime_identity_risk_signals"}]
