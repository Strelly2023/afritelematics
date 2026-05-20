from __future__ import annotations

from afritech.ci.four_gate_validator import validate


def test_four_gate_validator_enforces_system_contract() -> None:
    validate()
