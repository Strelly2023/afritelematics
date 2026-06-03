"""Tests for the Explainability Graph validator."""

from __future__ import annotations

from afritech.ci.explainability_graph_validator import (
    validate_explainability_graph,
)


def test_explainability_graph_validator_passes() -> None:
    validate_explainability_graph()