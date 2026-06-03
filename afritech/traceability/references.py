"""Canonical reference objects for governance traceability metadata."""

from __future__ import annotations

from dataclasses import dataclass


BRIDGE_STATUS = "REFERENCE_ONLY"
REFERENCE_ONLY = True
RUNTIME_AUTHORITY = False
ENFORCEMENT_AUTHORITY = False
PROJECTION_DEPENDENCY = False

ALLOWED_REFERENCE_TYPES = frozenset({"ADR", "INVARIANT", "RULE", "BINDING"})


@dataclass(frozen=True)
class GovernanceReference:
    """Identifier-only pointer to governance material."""

    ref_type: str
    ref_id: str

    def as_dict(self) -> dict[str, str]:
        return {
            "type": self.ref_type,
            "id": self.ref_id,
        }


@dataclass(frozen=True)
class TraceabilityBundle:
    """Immutable collection of governance reference pointers."""

    references: tuple[GovernanceReference, ...]

    @classmethod
    def from_references(
        cls, references: list[GovernanceReference] | tuple[GovernanceReference, ...]
    ) -> "TraceabilityBundle":
        return cls(references=tuple(references))

    def as_list(self) -> list[dict[str, str]]:
        return [reference.as_dict() for reference in self.references]
