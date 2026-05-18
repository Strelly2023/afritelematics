from afritech.semantic_engine.conflict.detector import SemanticConflict, detect_conflicts


def minimal_unsat(contracts) -> list[SemanticConflict]:
    return detect_conflicts(contracts)


def first_unsat(contracts) -> SemanticConflict | None:
    conflicts = minimal_unsat(contracts)
    return conflicts[0] if conflicts else None
