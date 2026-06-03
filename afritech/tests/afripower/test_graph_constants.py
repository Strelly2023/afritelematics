from __future__ import annotations

import pytest

from afritech.afripower.graph import constants as graph_constants


def test_graph_identity():
    assert graph_constants.GRAPH_COMPONENT == "AFRIPowerGraph"
    assert graph_constants.GRAPH_COMPONENT_ID == "afritech.afripower.graph"
    assert graph_constants.GRAPH_VERSION == "1.0"


def test_graph_mode_and_status():
    assert graph_constants.GRAPH_STATUS == "ENTERPRISE_INTELLIGENCE_PROJECTION"
    assert graph_constants.GRAPH_MODE == "READ_ONLY_ENTERPRISE_INTELLIGENCE_GRAPH"


def test_graph_safe_flags_are_true():
    assert graph_constants.GRAPH_READ_ONLY is True
    assert graph_constants.GRAPH_REFERENCE_ONLY is True
    assert graph_constants.GRAPH_DISPLAY_ONLY is True
    assert graph_constants.GRAPH_PROJECTION_ONLY is True
    assert graph_constants.GRAPH_ENTERPRISE_INTELLIGENCE_ONLY is True


def test_graph_authority_flags_are_false():
    assert graph_constants.GRAPH_AUTHORITATIVE is False
    assert graph_constants.GRAPH_CREATES_AUTHORITY is False
    assert graph_constants.GRAPH_VALIDATES_TRUTH is False
    assert graph_constants.GRAPH_EXECUTES_RUNTIME is False
    assert graph_constants.GRAPH_MUTATES_ARTIFACTS is False
    assert graph_constants.GRAPH_INFLUENCES_RUNTIME is False
    assert graph_constants.GRAPH_INFLUENCES_REPLAY is False
    assert graph_constants.GRAPH_INFLUENCES_PROOF is False
    assert graph_constants.GRAPH_INFLUENCES_CI is False
    assert graph_constants.GRAPH_INFLUENCES_GOVERNANCE is False


def test_graph_node_types_include_core_surfaces():
    assert "Execution" in graph_constants.GRAPH_NODE_TYPES
    assert "Proof" in graph_constants.GRAPH_NODE_TYPES
    assert "ADR" in graph_constants.GRAPH_NODE_TYPES
    assert "Invariant" in graph_constants.GRAPH_NODE_TYPES
    assert "Receipt" in graph_constants.GRAPH_NODE_TYPES
    assert "Traceability" in graph_constants.GRAPH_NODE_TYPES


def test_graph_edge_types_include_reference_edges():
    assert "references" in graph_constants.GRAPH_EDGE_TYPES
    assert "explains" in graph_constants.GRAPH_EDGE_TYPES
    assert "supports" in graph_constants.GRAPH_EDGE_TYPES
    assert "projects" in graph_constants.GRAPH_EDGE_TYPES


def test_graph_required_node_keys():
    assert graph_constants.GRAPH_REQUIRED_NODE_KEYS == (
        "node_id",
        "node_type",
    )


def test_graph_required_edge_keys():
    assert graph_constants.GRAPH_REQUIRED_EDGE_KEYS == (
        "source_id",
        "target_id",
        "relation",
    )


def test_graph_metadata_is_dictionary():
    metadata = graph_constants.graph_metadata()

    assert isinstance(metadata, dict)


def test_graph_metadata_preserves_boundary():
    metadata = graph_constants.graph_metadata()

    assert metadata["component"] == "AFRIPowerGraph"
    assert metadata["read_only"] is True
    assert metadata["reference_only"] is True
    assert metadata["display_only"] is True
    assert metadata["projection_only"] is True
    assert metadata["enterprise_intelligence_only"] is True
    assert metadata["authoritative"] is False
    assert metadata["creates_authority"] is False
    assert metadata["validates_truth"] is False
    assert metadata["executes_runtime"] is False
    assert metadata["mutates_artifacts"] is False


def test_graph_metadata_is_deterministic():
    assert graph_constants.graph_metadata() == graph_constants.graph_metadata()


def test_assert_graph_constants_passes():
    graph_constants.assert_graph_constants()


def test_assert_graph_constants_fails_on_authority(monkeypatch):
    monkeypatch.setattr(graph_constants, "GRAPH_AUTHORITATIVE", True)

    with pytest.raises(RuntimeError):
        graph_constants.assert_graph_constants()


def test_assert_graph_constants_fails_on_truth_validation(monkeypatch):
    monkeypatch.setattr(graph_constants, "GRAPH_VALIDATES_TRUTH", True)

    with pytest.raises(RuntimeError):
        graph_constants.assert_graph_constants()


def test_assert_graph_constants_fails_on_runtime_execution(monkeypatch):
    monkeypatch.setattr(graph_constants, "GRAPH_EXECUTES_RUNTIME", True)

    with pytest.raises(RuntimeError):
        graph_constants.assert_graph_constants()


def test_assert_graph_constants_fails_on_mutation(monkeypatch):
    monkeypatch.setattr(graph_constants, "GRAPH_MUTATES_ARTIFACTS", True)

    with pytest.raises(RuntimeError):
        graph_constants.assert_graph_constants()


def test_assert_graph_constants_fails_on_missing_read_only(monkeypatch):
    monkeypatch.setattr(graph_constants, "GRAPH_READ_ONLY", False)

    with pytest.raises(RuntimeError):
        graph_constants.assert_graph_constants()
