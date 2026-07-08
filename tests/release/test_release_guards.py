from __future__ import annotations

import pytest

from afritech.guards.guard_activation_gate import validate as validate_activation_gates
from afritech.guards.guard_ga_enablement import validate as validate_ga_enablement
from afritech.guards.guard_prr import validate as validate_prr
from afritech.guards.guard_release_stage import validate as validate_release_stage


pytestmark = [pytest.mark.release]


def test_all_release_guards_validate_current_framework() -> None:
    assert validate_release_stage()["status"] == "PASS"
    assert validate_activation_gates()["status"] == "PASS"
    assert validate_prr()["status"] == "PASS"
    assert validate_ga_enablement()["status"] == "PASS"

