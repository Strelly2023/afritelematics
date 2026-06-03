"""Tests for Explainability Graph edges."""

from __future__ import annotations

import pytest

from afritech.explainability_graph.edge import (
    build_graph_edge,
    graph_edge_to_dict,
)


def test_graph_edge_is_display_only_and_non_authoritative() -> None:
    edge = build_graph_edge(
        source_id="execution-001",
        target_id="ADR-0016",
        relation="governed_by",
    )

    payload = graph_edge_to_dict(edge)

    assert payload["source_id"] == "execution-001"
    assert payload["target_id"] == "ADR-0016"
    assert payload["relation"] == "governed_by"

    assert payload["read_only"] is True
    assert payload["display_only"] is True
    assert payload["non_authoritative"] is True
    assert payload["runtime_authority"] is False
    assert payload["validation_authority"] is False

    assert payload["influences_runtime"] is False
    assert payload["influences_replay"] is False
    assert payload["influences_proof"] is False


def test_graph_edge_rejects_unsupported_relation() -> None:
    with pytest.raises(ValueError):
        build_graph_edge(
            source_id="execution-001",
            target_id="ADR-0016",
            relation="decides",
        )


def test_graph_edge_rejects_empty_source() -> None:
    with pytest.raises(ValueError):
        build_graph_edge(
            source_id="",
            target_id="ADR-0016",
            relation="governed_by",
        )


def test_graph_edge_rejects_empty_target() -> None:
    with pytest.raises(ValueError):
        build_graph_edge(
            source_id="execution-001",
            target_id="",
            relation="governed_by",
        )