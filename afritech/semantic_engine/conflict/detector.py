from dataclasses import dataclass

from afritech.core.runtime.system_enforcement.execution_guard import admit_contract


@dataclass(frozen=True)
class SemanticConflict:
    contract_id: str
    reason: str
    trace: list[dict]


def detect_conflict(contract) -> SemanticConflict | None:
    result = admit_contract(contract)
    if result["status"] == "ADMIT":
        return None
    return SemanticConflict(
        contract_id=str(getattr(contract, "get", lambda _k, _d=None: _d)("id", "contract"))
        if isinstance(contract, dict)
        else str(contract),
        reason=result.get("reason", "SYSTEM_INVALID"),
        trace=result.get("trace", []),
    )


def detect_conflicts(contracts) -> list[SemanticConflict]:
    conflicts = []
    for contract in contracts:
        conflict = detect_conflict(contract)
        if conflict is not None:
            conflicts.append(conflict)
    return conflicts
