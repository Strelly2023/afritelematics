from __future__ import annotations

import pytest

from afritech.platform_contracts.federation import (
    FederationManifest,
    local_federation_manifest,
    negotiate_federation_manifest,
)
from afritech.platform_contracts.registry import (
    ContractRegistryError,
    architecture_metrics,
    capability_graph,
    negotiate_version,
    schema_publication,
    validate_contract_payload,
    validate_event_lineage,
    validate_tenant_lineage,
)
from afritech.platform_contracts.sdk_generator import generate_sdks


def test_version_negotiation_classifies_compatibility() -> None:
    assert negotiate_version("contract", "2.0.0").status == "COMPATIBLE"
    assert negotiate_version("contract", "2.0").status == "COMPATIBLE"
    assert negotiate_version("contract", "2.1.0").status == "UPGRADE_REQUIRED"
    assert negotiate_version("contract", "3.0.0").status == "UNSUPPORTED"


def test_schema_publications_are_signed_and_digest_bound() -> None:
    publication = schema_publication("request")

    assert publication["schema_digest"]
    assert publication["signature"]["scheme"] == "ed25519"
    assert publication["contract_version"] == "2.0.0"


def test_canonical_request_schema_rejects_missing_tenant() -> None:
    with pytest.raises(ContractRegistryError, match="tenant_id"):
        validate_contract_payload(
            "request",
            {
                "request_id": "request-1",
                "operation": "payment.execute",
                "actor_id": "actor-1",
                "idempotency_key": "idem-key-1",
                "contract_version": "2.0.0",
                "schema_version": "1.0.0",
                "payload": {},
            },
        )


def test_tenant_lineage_must_remain_end_to_end() -> None:
    with pytest.raises(ContractRegistryError, match="tenant_lineage_mismatch"):
        validate_tenant_lineage(
            tenant_id="tenant-a",
            policy={"tenant_id": "tenant-a"},
            execution={"tenant_id": "tenant-a"},
            event={"tenant_id": "tenant-b"},
            trust={"tenant_id": "tenant-a"},
            replay={"tenant_id": "tenant-a"},
        )


def test_event_lineage_links_command_to_integration_event() -> None:
    validate_event_lineage(
        command_id="command-1",
        policy_decision_id="policy-1",
        execution_id="execution-1",
        domain_event={
            "event_id": "domain-1",
            "causation_id": "execution-1",
            "correlation_id": "command-1",
            "policy_decision_id": "policy-1",
        },
        trust_event={
            "event_id": "trust-1",
            "causation_id": "domain-1",
            "correlation_id": "execution-1",
        },
        integration_event={
            "event_id": "integration-1",
            "causation_id": "trust-1",
            "correlation_id": "domain-1",
        },
    )


def test_capability_graph_and_metrics_are_complete() -> None:
    assert capability_graph()["acyclic"] is True
    assert architecture_metrics()["overall"] == 100


def test_federation_negotiates_versions_and_algorithm() -> None:
    result = negotiate_federation_manifest(local_federation_manifest("peer-1"))

    assert result["status"] == "COMPATIBLE"
    assert result["selected_signature_algorithm"] == "ed25519"

    elevated = FederationManifest(
        node_id="peer-2",
        versions=local_federation_manifest().versions,
        signature_algorithms=("ed25519",),
        capabilities=("remote_replay",),
        authority_boundary="execution",
    )
    with pytest.raises(
        ContractRegistryError, match="federation_peer_requests_execution_authority"
    ):
        negotiate_federation_manifest(elevated)


def test_sdk_generator_emits_all_supported_languages(tmp_path) -> None:
    paths = generate_sdks(tmp_path)

    assert {path.name for path in paths} == {
        "novatech_contracts.py",
        "novatech-contracts.ts",
        "NovaTechContracts.kt",
        "NovaTechContracts.swift",
    }
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "Generated from afritech/platform_contracts/platform.yaml" in text
        assert "2.0.0" in text
        assert "1.0.0" in text
