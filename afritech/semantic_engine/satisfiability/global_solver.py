from afritech.core.runtime.system_enforcement.execution_guard import admit_contract


def solve_all(contracts) -> list[dict]:
    return [admit_contract(contract) for contract in contracts]


def all_admissible(contracts) -> bool:
    return all(result["status"] == "ADMIT" for result in solve_all(contracts))
