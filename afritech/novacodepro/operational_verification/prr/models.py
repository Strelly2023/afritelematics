from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PRRDomainResult:
    domain: str
    status: str
    evidence_refs: tuple[str, ...] = ()
    findings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PRRPackage:
    prr_id: str
    release_id: str
    environment: str
    evidence_manifest_hash: str
    domains: tuple[PRRDomainResult, ...]
    recommendation: str
    ga_allowed: bool = False
    real_payments_enabled: bool = False
    signature_assurance: str = "DEVELOPMENT_ONLY"


@dataclass(frozen=True, slots=True)
class PRRFinding:
    id: str
    severity: str
    status: str
    summary: str


@dataclass(frozen=True, slots=True)
class PRRException:
    id: str
    approver: str
    expires_at: str
    scope: dict[str, object] = field(default_factory=dict)
