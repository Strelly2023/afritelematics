from __future__ import annotations

from afritech.ci.resilience_hardening_validator import validate


def test_resilience_hardening_validator_passes():
    assert validate() is True
