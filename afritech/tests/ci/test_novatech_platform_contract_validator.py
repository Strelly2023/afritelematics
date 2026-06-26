from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
import yaml

from afritech.ci.novatech_platform_contract_validator import (
    PlatformContractValidator,
    PlatformContractViolation,
    validate,
)


ROOT = Path(__file__).resolve().parents[3]


def test_novatech_platform_contract_is_machine_verifiable() -> None:
    assert validate() is True


def test_validator_rejects_upward_capability_dependency(tmp_path: Path) -> None:
    source = ROOT / "afritech/platform_contracts/platform.yaml"
    contract = yaml.safe_load(source.read_text(encoding="utf-8"))
    contract = deepcopy(contract)
    contract["capabilities"][0]["depends_on"] = ["products"]

    with pytest.raises(PlatformContractViolation, match="upward_capability_dependency"):
        PlatformContractValidator(tmp_path)._validate_capabilities(contract)


def test_all_governed_data_schemas_fail_closed() -> None:
    contract = yaml.safe_load(
        (ROOT / "afritech/platform_contracts/platform.yaml").read_text(encoding="utf-8")
    )
    for relative_path in contract["data_contracts"].values():
        schema = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
        assert schema["additionalProperties"] is False
