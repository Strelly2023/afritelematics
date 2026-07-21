from __future__ import annotations

import pytest

from afritech.novaid.runtime import validate_runtime_environment


def test_novaid_production_requires_postgres() -> None:
    with pytest.raises(RuntimeError, match="production_novaid_requires_postgres"):
        validate_runtime_environment("production", "sqlite")


def test_novaid_non_production_allows_sqlite() -> None:
    validate_runtime_environment("development", "sqlite")
