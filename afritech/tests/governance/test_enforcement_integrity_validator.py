from __future__ import annotations

from afritech.ci.enforcement_integrity_validator import validate


def test_enforcement_integrity_validator_protects_gate() -> None:
    validate()
