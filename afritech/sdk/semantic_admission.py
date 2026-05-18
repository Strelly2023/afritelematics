from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from afritech.runtime.system_enforcement.execution_guard import admit_contract
from afritech.semantic_engine.inspection import inspect_admission


class SemanticAdmissionClient:
    def admit(
        self,
        contract: str | Path | dict[str, Any],
        truth_values: dict[str, bool] | None = None,
        *,
        inspect: bool = False,
    ) -> dict[str, Any]:
        result = admit_contract(contract, truth_values=truth_values)
        if inspect:
            return {
                "result": result,
                "inspection": inspect_admission(result),
            }
        return result

    def admit_yaml_text(
        self,
        yaml_text: str,
        truth_values: dict[str, bool] | None = None,
        *,
        inspect: bool = False,
    ) -> dict[str, Any]:
        payload = yaml.safe_load(yaml_text)
        if not isinstance(payload, dict):
            raise ValueError("contract YAML must be a mapping")
        return self.admit(payload, truth_values=truth_values, inspect=inspect)

    def prepare_api_payload(
        self,
        contract: dict[str, Any],
        truth_values: dict[str, bool] | None = None,
        *,
        include_trace: bool = True,
    ) -> dict[str, Any]:
        return {
            "contract": contract,
            "truth_values": truth_values,
            "include_trace": include_trace,
        }
