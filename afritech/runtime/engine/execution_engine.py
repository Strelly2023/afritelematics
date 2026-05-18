from pathlib import Path
from typing import Any

from afritech.runtime.system_enforcement.execution_guard import admit_contract


class SemanticExecutionEngine:
    def admit(
        self,
        contract: str | Path | dict[str, Any],
        truth_values: dict[str, bool] | None = None,
    ) -> dict[str, Any]:
        return admit_contract(contract, truth_values=truth_values)
