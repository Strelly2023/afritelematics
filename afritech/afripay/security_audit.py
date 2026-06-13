"""Append-only security audit stream for AfriPay proof validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any, Mapping


AUTHORITY_DISCLAIMER = "security audit stream is evidence-only and non-authoritative"


@dataclass(frozen=True)
class SecurityAuditRecord:
    event_type: str
    actor: str
    details: Mapping[str, Any]
    previous_hash: str
    hash_chain: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "actor": self.actor,
            "details": dict(sorted(self.details.items())),
            "event_type": self.event_type,
            "hash_chain": self.hash_chain,
            "previous_hash": self.previous_hash,
            "schema": "afritech.afripay.security_audit_record.v1",
        }


@dataclass
class SecurityAuditStream:
    authority_disclaimer: str = AUTHORITY_DISCLAIMER
    _records: list[SecurityAuditRecord] = field(default_factory=list)

    def append(self, event_type: str, *, actor: str, details: Mapping[str, Any]) -> SecurityAuditRecord:
        previous_hash = self._records[-1].hash_chain if self._records else "GENESIS"
        payload = {
            "actor": actor,
            "details": dict(sorted(details.items())),
            "event_type": event_type,
            "previous_hash": previous_hash,
        }
        record = SecurityAuditRecord(
            event_type=event_type,
            actor=actor,
            details=dict(details),
            previous_hash=previous_hash,
            hash_chain=_canonical_hash(payload),
        )
        self._records.append(record)
        return record

    def extend(self, records: list[tuple[str, str, Mapping[str, Any]]]) -> tuple[SecurityAuditRecord, ...]:
        appended: list[SecurityAuditRecord] = []
        for event_type, actor, details in records:
            appended.append(self.append(event_type, actor=actor, details=details))
        return tuple(appended)

    def root_hash(self) -> str:
        return _canonical_hash(
            {
                "authority_disclaimer": self.authority_disclaimer,
                "records": [record.canonical_dict() for record in self._records],
            }
        )

    def verify(self) -> bool:
        previous_hash = "GENESIS"
        for record in self._records:
            expected_hash = _canonical_hash(
                {
                    "actor": record.actor,
                    "details": dict(sorted(record.details.items())),
                    "event_type": record.event_type,
                    "previous_hash": previous_hash,
                }
            )
            if expected_hash != record.hash_chain:
                return False
            previous_hash = record.hash_chain
        return self.authority_disclaimer == AUTHORITY_DISCLAIMER

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "record_count": len(self._records),
            "records": [record.canonical_dict() for record in self._records],
            "root_hash": self.root_hash(),
            "schema": "afritech.afripay.security_audit_stream.v1",
            "verified": self.verify(),
        }

    @property
    def records(self) -> tuple[SecurityAuditRecord, ...]:
        return tuple(self._records)


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()
