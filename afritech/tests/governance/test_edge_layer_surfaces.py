from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
import yaml

from afritech.edge.adapter.runtime_adapter import adapt_request
from afritech.edge.adapter.validation import validate_adapted_request
from afritech.edge.ingestion.queue_ingestor import ingest_event
from afritech.edge.normalization.normalizer import normalize_input
from afritech.edge.normalization.validation import validate_normalized_input
from afritech.guards.edge_input_guard import validate_edge_pipeline


ROOT = Path(__file__).resolve().parents[3]
SURFACE_AUTHORITY = ROOT / "afritech/architecture/surface_authority_registry.yaml"
SURFACE_BINDING = ROOT / "afritech/architecture/surface_implementation_binding.yaml"
IMPLEMENTATION_REGISTRY = ROOT / "afritech/architecture/implementation_registry.yaml"
EXECUTION_SURFACES = ROOT / "afritech/governance/EXECUTION_SURFACES.yaml"
EDGE_RULE = ROOT / "afritech/governance/rules/RULE-EDGE-001.yaml"
EDGE_ADR = ROOT / "afritech/governance/adr/ADR-0012-edge-layer-admission.yaml"
SEMANTIC_CHECKS = ROOT / "afritech/ci/semantic_integrity_checks.yaml"


EDGE_SURFACE_KEYS = {
    "edge_adapter": "afritech.edge.adapter",
    "edge_normalization": "afritech.edge.normalization",
    "edge_ingestion": "afritech.edge.ingestion",
}

EDGE_IMPLEMENTATIONS = (
    "afritech.edge.adapter.runtime_adapter",
    "afritech.edge.adapter.validation",
    "afritech.edge.normalization.normalizer",
    "afritech.edge.normalization.validation",
    "afritech.edge.ingestion.queue_ingestor",
    "afritech.guards.edge_input_guard",
)


@dataclass
class MemoryQueue:
    events: list[dict[str, Any]] = field(default_factory=list)

    def publish(self, event: dict[str, Any]) -> None:
        self.events.append(event)


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_edge_surfaces_are_declared_in_authority_registry() -> None:
    registry = load_yaml(SURFACE_AUTHORITY)
    surfaces = registry["surfaces"]

    for surface_key, canonical_identity in EDGE_SURFACE_KEYS.items():
        surface = surfaces[surface_key]
        assert surface["canonical_identity"] == canonical_identity
        assert surface["implementation_state"] == "IMPLEMENTED"
        assert surface["runtime_admissible"] is True
        assert surface["replay_participating"] is True
        assert surface["proof_admissible"] is True
        assert surface["deterministic_required"] is True
        assert surface["replay_safe_required"] is True
        assert surface["closed_world_required"] is True


def test_edge_surfaces_are_bound_to_implementations() -> None:
    registry = load_yaml(SURFACE_BINDING)
    bindings = registry["bindings"]

    assert (
        bindings["edge_adapter"]["implementation_bindings"]["runtime_activation"][
            "implementation"
        ]
        == "afritech.edge.adapter.runtime_adapter"
    )
    assert (
        bindings["edge_normalization"]["implementation_bindings"][
            "runtime_activation"
        ]["implementation"]
        == "afritech.edge.normalization.normalizer"
    )
    assert (
        bindings["edge_ingestion"]["implementation_bindings"]["runtime_activation"][
            "implementation"
        ]
        == "afritech.edge.ingestion.queue_ingestor"
    )
    assert (
        bindings["edge_ingestion"]["implementation_bindings"]["replay"][
            "implementation"
        ]
        == "afritech.trace.trace_reconstructor"
    )


def test_edge_implementations_are_registered_as_replay_safe() -> None:
    registry = load_yaml(IMPLEMENTATION_REGISTRY)
    implementations = registry["implementations"]

    for implementation in EDGE_IMPLEMENTATIONS:
        entry = implementations[implementation]
        assert entry["implementation_state"] == "IMPLEMENTED"
        assert entry["ontology"] == "CANONICAL_MODULE_PATH"
        assert entry["semantic_properties"]["deterministic_execution"] is True
        assert entry["semantic_properties"]["replay_admissible"] is True
        assert entry["semantic_properties"]["proof_admissible"] is True
        assert entry["semantic_properties"]["closed_world_aligned"] is True
        assert entry["semantic_properties"]["replay_safe"] is True


def test_edge_surfaces_are_closed_world_execution_surfaces() -> None:
    registry = load_yaml(EXECUTION_SURFACES)
    allowed = registry["allowed_execution_surfaces"]

    for surface_key in EDGE_SURFACE_KEYS:
        surface = allowed[surface_key]
        assert surface["status"] == "CANONICAL"
        assert surface["paths"]
        assert "direct_runtime_execution" in surface["forbidden_operations"]


def test_edge_rule_and_ci_check_are_present() -> None:
    rule = load_yaml(EDGE_RULE)
    checks = load_yaml(SEMANTIC_CHECKS)

    assert rule["id"] == "RULE-EDGE-001"
    assert rule["enforcement"]["runtime"] is True
    assert rule["enforcement"]["replay"] is True
    assert rule["required_sequence"] == ["adapter", "normalization", "ingestion"]
    assert "direct_external_runtime_execution" in rule["forbidden"]

    check_ids = {check["id"] for check in checks["checks"]}
    assert "CI-EDGE-001" in check_ids


def test_edge_layer_has_constitutional_adr() -> None:
    adr = load_yaml(EDGE_ADR)["adr"]

    assert adr["id"] == "ADR-0012"
    assert adr["status"] == "ACCEPTED"
    assert adr["type"] == "CONSTITUTIONAL_EXECUTION_TOPOLOGY"
    assert adr["classification"]["execution_surface_effect"] == (
        "DECLARED_CANONICAL_EDGE_SURFACES"
    )

    for surface in EDGE_SURFACE_KEYS.values():
        assert surface in adr["admitted_surfaces"]

    assert "RULE-EDGE-001" in adr["required_rule"]
    assert "afritech.guards.edge_input_guard" in adr["required_guard"]
    assert "CI-EDGE-001" in adr["required_ci_checks"]
    assert "direct_external_runtime_execution" in adr["forbidden"]


def test_edge_pipeline_is_deterministic_and_queue_mediated() -> None:
    raw_input = {
        "request_id": 123,
        "timestamp": "1700000000999",
        "payload": {"destination": "Airport", "origin": "CBD"},
    }
    same_input_different_order = {
        "timestamp": "1700000000999",
        "payload": {"origin": "CBD", "destination": "Airport"},
        "request_id": 123,
    }

    adapted = adapt_request(raw_input)
    adapted_again = adapt_request(same_input_different_order)
    validate_adapted_request(adapted)

    normalized = normalize_input(adapted)
    normalized_again = normalize_input(adapted_again)
    validate_normalized_input(normalized)

    assert normalized == normalized_again
    assert normalized["timestamp_bucket"] == 1700000000

    queue = MemoryQueue()
    ingest_event(normalized, queue)

    assert queue.events == [normalized]


def test_edge_pipeline_guard_requires_adapter_normalization_ingestion_order() -> None:
    validate_edge_pipeline({"stages": ["adapter", "normalization", "ingestion"]})

    with pytest.raises(ValueError, match="Edge pipeline violated"):
        validate_edge_pipeline({"stages": ["normalization", "adapter", "ingestion"]})

    with pytest.raises(ValueError, match="ordered stages"):
        validate_edge_pipeline({"stages": "adapter"})
