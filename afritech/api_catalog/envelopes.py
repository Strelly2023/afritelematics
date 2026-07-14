"""Canonical API response envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ResponseMeta:
    request_id: str
    trace_id: str
    contract_version: str
    organization_id: str | None = None


@dataclass(frozen=True, slots=True)
class EvidenceRefs:
    replay_id: str | None = None
    receipt_id: str | None = None
    audit_id: str | None = None
    proof_hash: str | None = None


def success_envelope(data: Any, *, meta: ResponseMeta, evidence: EvidenceRefs | None = None) -> dict[str, Any]:
    return {
        "data": data,
        "meta": {
            "request_id": meta.request_id,
            "trace_id": meta.trace_id,
            "contract_version": meta.contract_version,
            "organization_id": meta.organization_id,
        },
        "evidence": (
            {
                "replay_id": evidence.replay_id,
                "receipt_id": evidence.receipt_id,
                "audit_id": evidence.audit_id,
                "proof_hash": evidence.proof_hash,
            }
            if evidence
            else None
        ),
        "errors": [],
    }


def error_envelope(*, code: str, message: str, trace_id: str, retryable: bool = False, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "data": None,
        "meta": {"trace_id": trace_id},
        "evidence": None,
        "errors": [{"code": code, "message": message, "retryable": retryable, "details": details or {}}],
    }
