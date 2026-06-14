"""Unified mobility participant model for AfriID Gen-3 surfaces."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any


SCHEMA = "afritech.identity.mobility_participant.v1"
AUTHORITY_BOUNDARY = "mobility_identity_reference_only"

ALLOWED_MOBILITY_ROLES = (
    "rider",
    "driver",
    "courier",
    "merchant",
    "fleet",
    "institution",
)

ALLOWED_VERIFICATION_STATUSES = (
    "unverified",
    "pending",
    "verified",
    "suspended",
)


class MobilityParticipantError(ValueError):
    """Raised when a mobility participant payload is invalid."""


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MobilityParticipantError(f"{label} is required")
    return value.strip()


def _normalize_roles(values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise MobilityParticipantError("roles must be iterable")
    normalized = tuple(
        _require_text(value, "role") for value in values if _require_text(value, "role")
    )
    if not normalized:
        raise MobilityParticipantError("at least one role is required")
    invalid = sorted({value for value in normalized if value not in ALLOWED_MOBILITY_ROLES})
    if invalid:
        raise MobilityParticipantError(
            "unsupported mobility role(s): " + ", ".join(invalid)
        )
    return tuple(sorted(set(normalized)))


def _normalize_links(values: Iterable[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise MobilityParticipantError("evidence_links must be iterable")
    normalized = tuple(
        _require_text(value, "evidence_link")
        for value in values
        if _require_text(value, "evidence_link")
    )
    return tuple(sorted(set(normalized)))


def _freeze_mapping(value: Mapping[str, object] | None) -> tuple[tuple[str, object], ...]:
    if value is None:
        return tuple()
    if not isinstance(value, Mapping):
        raise MobilityParticipantError("metadata must be a mapping")
    return tuple(sorted(value.items(), key=lambda item: str(item[0])))


@dataclass(frozen=True)
class MobilityParticipant:
    """Immutable identity reference for the Gen-3 mobility stack."""

    participant_id: str
    display_name: str
    roles: tuple[str, ...]
    verification_status: str = "unverified"
    trust_score: float = 0.0
    evidence_links: tuple[str, ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, object], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "participant_id", _require_text(self.participant_id, "participant_id"))
        object.__setattr__(self, "display_name", _require_text(self.display_name, "display_name"))
        object.__setattr__(self, "roles", _normalize_roles(self.roles))
        if self.verification_status not in ALLOWED_VERIFICATION_STATUSES:
            raise MobilityParticipantError(
                f"unsupported verification_status: {self.verification_status}"
            )
        if not isinstance(self.trust_score, (int, float)):
            raise MobilityParticipantError("trust_score must be numeric")
        if not 0.0 <= float(self.trust_score) <= 100.0:
            raise MobilityParticipantError("trust_score must be between 0 and 100")
        object.__setattr__(self, "trust_score", round(float(self.trust_score), 6))
        object.__setattr__(self, "evidence_links", _normalize_links(self.evidence_links))
        object.__setattr__(self, "metadata", _freeze_mapping(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "MobilityParticipant":
        if not isinstance(payload, Mapping):
            raise MobilityParticipantError("participant payload must be a mapping")
        raw_roles = payload.get("roles", ())
        raw_links = payload.get("evidence_links", ())
        return cls(
            participant_id=_require_text(payload.get("participant_id") or payload.get("id"), "participant_id"),
            display_name=_require_text(payload.get("display_name") or payload.get("name"), "display_name"),
            roles=tuple(raw_roles),  # type: ignore[arg-type]
            verification_status=_require_text(
                payload.get("verification_status"), "verification_status"
            ),
            trust_score=float(payload.get("trust_score", 0.0)),
            evidence_links=tuple(raw_links),  # type: ignore[arg-type]
            metadata=_freeze_mapping(payload.get("metadata", {})),
        )

    @property
    def multi_role(self) -> bool:
        return len(self.roles) > 1

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "authority_boundary": AUTHORITY_BOUNDARY,
            "participant_id": self.participant_id,
            "display_name": self.display_name,
            "roles": self.roles,
            "multi_role": self.multi_role,
            "verification_status": self.verification_status,
            "trust_score": self.trust_score,
            "evidence_links": self.evidence_links,
            "metadata": dict(self.metadata),
            "identity_is_reference_only": True,
            "identity_is_truth_authority": False,
            "identity_overrides_replay": False,
            "identity_overrides_proof": False,
            "identity_overrides_payment": False,
            "identity_overrides_runtime_admissibility": False,
        }

    def participant_hash(self) -> str:
        encoded = json.dumps(
            self.canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        return sha256(encoded).hexdigest()


def validate_mobility_participant(
    payload: Mapping[str, object] | MobilityParticipant,
) -> MobilityParticipant:
    if isinstance(payload, MobilityParticipant):
        return payload
    if not isinstance(payload, Mapping):
        raise MobilityParticipantError("participant payload must be a mapping")
    return MobilityParticipant.from_mapping(payload)
