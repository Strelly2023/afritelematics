from dataclasses import dataclass

from afritech.semantic_engine.conflict.detector import SemanticConflict


@dataclass(frozen=True)
class ConflictResolution:
    status: str
    reason: str
    conflict: SemanticConflict | None = None


def resolve_conflict(conflict: SemanticConflict | None) -> ConflictResolution:
    if conflict is None:
        return ConflictResolution(status="ADMIT", reason="no_conflict")
    return ConflictResolution(
        status="SYSTEM_INVALID",
        reason=conflict.reason,
        conflict=conflict,
    )
