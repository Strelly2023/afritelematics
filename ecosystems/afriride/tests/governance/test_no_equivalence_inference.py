"""Frozen test placeholder for ecosystems.afriride.tests.governance.test_no_equivalence_inference."""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.skip(
    reason=(
        "FROZEN: this test surface is declared but has no admitted "
        "runtime behavior in the current epoch"
    )
)
