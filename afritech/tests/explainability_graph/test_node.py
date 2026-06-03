"""Tests for Explainability Graph nodes."""

from __future__ import annotations

import pytest

from afritech.explainability_graph.node import (
    build_graph_node,
    graph_node_to_dict,
)


def test_graph_node_is_display_only_and_non_authoritative() -> None:
    node = build_graph_node(
        node_type="Execution",
        node_id="execution-001",
        label="Execution 001",
    )

    payload = graph_node_to_dict(node)

    assert payload["type"] == "Execution"
    assert payload["id"] == "execution-001"
    assert payload["label"] == "Execution 001"

    assert payload["read_only"] is True
    assert payload["display_only"] is True
    assert payload["non_authoritative"] is True
    assert payload["runtime_authority"] is False
    assert payload["validation_authority"] is False


def test_graph_node_uses_id_as_default_label() -> None:
    node = build_graph_node(
        node_type="ADR",
        node_id="ADR-0016",
    )

    payload = graph_node_to_dict(node)

    assert payload["label"] == "ADR-0016"


def test_graph_node_rejects_unsupported_type() -> None:
    with pytest.raises(ValueError):
        build_graph_node(
            node_type="Runtime",
            node_id="runtime-001",
        )


def test_graph_node_rejects_empty_id() -> None:
    with pytest.raises(ValueError):
        build_graph_node(
            node_type="Execution",
            node_id="",
        )