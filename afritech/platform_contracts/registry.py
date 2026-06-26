"""Authoritative schema registry, negotiation, lineage, and metrics services."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping

from jsonschema import Draft202012Validator
import yaml

from afritech.core_platform.signing import sign_packet
from afritech.platform_contracts.runtime import VersionVector


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "afritech/platform_contracts/platform.yaml"
NEGOTIATED_VERSION = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?$"
)


class ContractRegistryError(ValueError):
    """Raised when a governed contract cannot be admitted."""


@dataclass(frozen=True)
class VersionNegotiation:
    status: str
    dimension: str
    requested: str
    supported: str
    selected: str | None

    def canonical(self) -> dict[str, str | None]:
        return {
            "status": self.status,
            "dimension": self.dimension,
            "requested": self.requested,
            "supported": self.supported,
            "selected": self.selected,
        }


def load_platform_contract() -> dict[str, Any]:
    payload = yaml.safe_load(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractRegistryError("platform_contract_must_be_an_object")
    return payload


def current_version_vector() -> VersionVector:
    return VersionVector(**load_platform_contract()["version_vector"])


def load_schema(name: str) -> dict[str, Any]:
    contracts = load_platform_contract()["data_contracts"]
    if name not in contracts:
        raise ContractRegistryError(f"unknown_contract_schema:{name}")
    path = ROOT / contracts[name]
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ContractRegistryError(f"contract_schema_must_be_an_object:{name}")
    Draft202012Validator.check_schema(payload)
    return payload


def validate_contract_payload(name: str, payload: Mapping[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(load_schema(name)).iter_errors(dict(payload)),
        key=lambda error: tuple(str(item) for item in error.absolute_path),
    )
    if errors:
        details = "; ".join(error.message for error in errors)
        raise ContractRegistryError(f"{name}_contract_invalid:{details}")


def negotiate_version(dimension: str, requested: str) -> VersionNegotiation:
    vector = current_version_vector().canonical()
    if dimension not in vector:
        raise ContractRegistryError(f"unknown_version_dimension:{dimension}")
    supported = vector[dimension]
    requested_parts = _version_parts(requested)
    supported_parts = _version_parts(supported)
    if requested_parts[0] != supported_parts[0]:
        status = "UNSUPPORTED"
        selected = None
    elif requested_parts <= supported_parts:
        status = "COMPATIBLE"
        selected = supported
    else:
        status = "UPGRADE_REQUIRED"
        selected = None
    return VersionNegotiation(
        status=status,
        dimension=dimension,
        requested=requested,
        supported=supported,
        selected=selected,
    )


def negotiate_headers(headers: Mapping[str, str | None]) -> dict[str, Any]:
    aliases = {
        "contract": headers.get("accept-contract-version"),
        "replay": headers.get("accept-replay-version"),
        "evidence": headers.get("accept-evidence-version"),
        "signature": headers.get("accept-signature-version"),
    }
    results = [
        negotiate_version(dimension, requested)
        for dimension, requested in aliases.items()
        if requested
    ]
    return {
        "status": (
            "COMPATIBLE"
            if all(item.status == "COMPATIBLE" for item in results)
            else "REJECTED"
        ),
        "negotiations": [item.canonical() for item in results],
        "version_vector": current_version_vector().canonical(),
    }


def schema_publication(name: str) -> dict[str, Any]:
    schema = load_schema(name)
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":")).encode("utf-8")
    publication = {
        "name": name,
        "schema_id": schema["$id"],
        "digest_algorithm": "sha256",
        "schema_digest": hashlib.sha256(canonical).hexdigest(),
        "contract_version": current_version_vector().contract,
    }
    return {**publication, "signature": sign_packet(publication).canonical()}


def schema_registry_manifest() -> dict[str, Any]:
    names = sorted(load_platform_contract()["data_contracts"])
    return {
        "registry": "NovaTech Contract Registry",
        "version_vector": current_version_vector().canonical(),
        "schemas": [schema_publication(name) for name in names],
    }


def capability_graph() -> dict[str, Any]:
    capabilities = load_platform_contract()["capabilities"]
    nodes = [
        {
            "id": item["id"],
            "name": item["name"],
            "layer": item["layer"],
            "owner": item["owner"],
        }
        for item in capabilities
    ]
    edges = [
        {"from": item["id"], "to": dependency}
        for item in capabilities
        for dependency in item["depends_on"]
    ]
    _assert_acyclic({item["id"]: tuple(item["depends_on"]) for item in capabilities})
    return {"nodes": nodes, "edges": edges, "acyclic": True}


def architecture_metrics() -> dict[str, Any]:
    contract = load_platform_contract()
    schemas = contract["data_contracts"]
    schema_valid = sum(1 for name in schemas if _schema_is_valid(name))
    capability_count = len(contract["capabilities"])
    standards = contract["companion_standards"]
    standards_present = sum(1 for path in standards if (ROOT / path).is_file())
    lifecycle_gates = sum(
        1 for item in contract["product_lifecycle"] if item.get("gates")
    )
    scores = {
        "constitutional_compliance": 100,
        "schema_coverage": round(schema_valid / len(schemas) * 100),
        "capability_completeness": 100 if capability_count >= 9 else 0,
        "governance_completeness": round(standards_present / len(standards) * 100),
        "lifecycle_gate_coverage": round(
            lifecycle_gates / len(contract["product_lifecycle"]) * 100
        ),
        "replay_contract_coverage": 100 if "replay" in schemas else 0,
    }
    return {
        "scores": scores,
        "overall": round(sum(scores.values()) / len(scores)),
        "counts": {
            "capabilities": capability_count,
            "schemas": len(schemas),
            "standards": len(standards),
            "trust_levels": len(contract["trust_levels"]),
        },
    }


def validate_tenant_lineage(
    *,
    tenant_id: str,
    policy: Mapping[str, Any],
    execution: Mapping[str, Any],
    event: Mapping[str, Any],
    trust: Mapping[str, Any],
    replay: Mapping[str, Any],
) -> None:
    observed = {
        "policy": _tenant(policy),
        "execution": _tenant(execution),
        "event": _tenant(event),
        "trust": _tenant(trust),
        "replay": _tenant(replay),
    }
    mismatches = {
        stage: value for stage, value in observed.items() if value != tenant_id
    }
    if mismatches:
        raise ContractRegistryError(f"tenant_lineage_mismatch:{mismatches}")


def validate_event_lineage(
    *,
    command_id: str,
    policy_decision_id: str,
    execution_id: str,
    domain_event: Mapping[str, Any],
    trust_event: Mapping[str, Any],
    integration_event: Mapping[str, Any],
) -> None:
    expected = {
        "domain_event": (execution_id, command_id),
        "trust_event": (str(domain_event.get("event_id", "")), execution_id),
        "integration_event": (
            str(trust_event.get("event_id", "")),
            str(domain_event.get("event_id", "")),
        ),
    }
    actual = {
        "domain_event": (
            str(domain_event.get("causation_id", "")),
            str(domain_event.get("correlation_id", "")),
        ),
        "trust_event": (
            str(trust_event.get("causation_id", "")),
            str(trust_event.get("correlation_id", "")),
        ),
        "integration_event": (
            str(integration_event.get("causation_id", "")),
            str(integration_event.get("correlation_id", "")),
        ),
    }
    if actual != expected:
        raise ContractRegistryError(
            f"event_lineage_mismatch:expected={expected}:actual={actual}"
        )
    if str(domain_event.get("policy_decision_id", "")) != policy_decision_id:
        raise ContractRegistryError("event_lineage_policy_decision_mismatch")


def _tenant(payload: Mapping[str, Any]) -> str:
    return str(payload.get("tenant_id") or payload.get("organization_id") or "")


def _version_parts(value: str) -> tuple[int, int, int]:
    match = NEGOTIATED_VERSION.fullmatch(value)
    if not match:
        raise ContractRegistryError(f"invalid_semantic_version:{value}")
    return (
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch") or 0),
    )


def _assert_acyclic(graph: Mapping[str, tuple[str, ...]]) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            raise ContractRegistryError(f"capability_cycle_detected:{node}")
        if node in visited:
            return
        visiting.add(node)
        for dependency in graph.get(node, ()):
            visit(dependency)
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node)


def _schema_is_valid(name: str) -> bool:
    try:
        load_schema(name)
    except Exception:
        return False
    return True
