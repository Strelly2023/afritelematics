from __future__ import annotations

from afritech.ci.afriprogramming_engineering_validator import (
    validate_afriprogramming_engineering_surface,
)
from afritech.ci.afriprog_afriprogramming_boundary_validator import (
    validate_afriprog_afriprogramming_boundary,
)


def test_validator_accepts_current_afriprogramming_surface():
    validate_afriprogramming_engineering_surface()


def test_boundary_validator_accepts_current_afriprog_to_afriprogramming_handoff():
    validate_afriprog_afriprogramming_boundary()
