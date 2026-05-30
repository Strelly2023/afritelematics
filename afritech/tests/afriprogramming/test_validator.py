from __future__ import annotations

from afritech.ci.afriprogramming_engineering_validator import (
    validate_afriprogramming_engineering_surface,
)


def test_validator_accepts_current_afriprogramming_surface():
    validate_afriprogramming_engineering_surface()
