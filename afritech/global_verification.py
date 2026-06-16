"""Level 15 global public verification layer.

This layer makes a signed feature registry portable across independent
verification networks. The default anchors are deterministic dry-run receipts;
live chain publication remains optional and is never required for CI.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from afritech.chain.types import ChainReceipt
from afritech.features import registry_payload
from afritech.tools.feature_registry_verifier import verify_registry_payload
from afritech.trust_federation import (
    build_federated_trust_certificate,
    verify_federated_trust_certificate,
)

REPORT_ROOT = Path(__file__).resolve().parents[1] / "reports" / "global_public_verification"


def _hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class InteroperabilityNetwork:
    network_id: str
    name: str
    protocol: str
    chain_id: int | None
    jurisdiction: str
    anchoring_mode: str

    def canonical_dict(self) -> dict[str, object]:
        return {
            "network_id": self.network_id,
            "name": self.name,
            "protocol": self.protocol,
            "chain_id": self.chain_id,
            "jurisdiction": self.jurisdiction,
            "anchoring_mode": self.anchoring_mode,
        }


@dataclass(frozen=True)
class CrossNetworkAnchor:
    network: InteroperabilityNetwork
    receipt: ChainReceipt
    receipt_hash: str
    optional_onchain: bool = True

    def canonical_dict(self) -> dict[str, object]:
        return {
            "network": self.network.canonical_dict(),
            "receipt": self.receipt.canonical_dict(),
            "receipt_hash": self.receipt_hash,
            "optional_onchain": self.optional_onchain,
        }


@dataclass(frozen=True)
class GlobalVerificationBundle:
    classification: str
    level: str
    status: str
    registry_hash: str
    federation_hash: str
    anchor_hash: str
    global_bundle_hash: str
    registry: dict[str, Any]
    federated_certificate: dict[str, Any]
    cross_network_anchors: tuple[CrossNetworkAnchor, ...]
    read_only: bool = True
    creates_authority: bool = False
    optional_onchain_anchor_supported: bool = True
    authority_boundary: str = "global_verification_exports_truth_without_creating_runtime_or_production_authority"

    def canonical_dict(self) -> dict[str, object]:
        return {
            "schema": "afritech.global_public_verification_bundle.v1",
            "classification": self.classification,
            "level": self.level,
            "status": self.status,
            "registry_hash": self.registry_hash,
            "federation_hash": self.federation_hash,
            "anchor_hash": self.anchor_hash,
            "global_bundle_hash": self.global_bundle_hash,
            "registry": self.registry,
            "federated_certificate": self.federated_certificate,
            "cross_network_anchors": [
                anchor.canonical_dict() for anchor in self.cross_network_anchors
            ],
            "read_only": self.read_only,
            "creates_authority": self.creates_authority,
            "optional_onchain_anchor_supported": self.optional_onchain_anchor_supported,
            "authority_boundary": self.authority_boundary,
            "guarantees": {
                "truth_independent_of_origin_system": True,
                "cross_network_interoperable": True,
                "global_public_verification_available": True,
                "optional_onchain_anchoring_supported": True,
                "no_fake_feature_can_exist": True,
                "no_incomplete_feature_can_appear": True,
                "no_unverifiable_claim_can_be_exported": True,
                "no_production_state_can_be_falsely_implied": True,
            },
        }


def default_interoperability_networks() -> tuple[InteroperabilityNetwork, ...]:
    return (
        InteroperabilityNetwork(
            network_id="afritech-federated-trust",
            name="AfriTech Federated Trust Network",
            protocol="federated-ed25519-quorum",
            chain_id=None,
            jurisdiction="multi-jurisdiction",
            anchoring_mode="native_quorum",
        ),
        InteroperabilityNetwork(
            network_id="ethereum-sepolia",
            name="Ethereum Sepolia",
            protocol="evm-anchor",
            chain_id=11155111,
            jurisdiction="public-testnet",
            anchoring_mode="optional_onchain",
        ),
        InteroperabilityNetwork(
            network_id="papc-public-ledger",
            name="PAPC Public Ledger",
            protocol="public-ledger-anchor",
            chain_id=None,
            jurisdiction="pan-african-public-ledger",
            anchoring_mode="deterministic_public_receipt",
        ),
    )


def build_global_verification_bundle(
    registry: dict[str, Any] | None = None,
    *,
    networks: tuple[InteroperabilityNetwork, ...] | None = None,
) -> GlobalVerificationBundle:
    payload = registry or registry_payload()
    registry_hash = str(payload["registry_hash"])
    federation = build_federated_trust_certificate(payload).canonical_dict()
    selected_networks = networks or default_interoperability_networks()
    anchors = tuple(_build_anchor(network, registry_hash) for network in selected_networks)
    anchor_hash = _hash([anchor.canonical_dict() for anchor in anchors])
    federation_hash = _hash(federation)
    base = {
        "classification": "LEVEL_15_GLOBAL_PUBLIC_VERIFICATION_LAYER",
        "level": "LEVEL_15",
        "status": "GLOBAL_PUBLIC_VERIFICATION_READY",
        "registry_hash": registry_hash,
        "federation_hash": federation_hash,
        "anchor_hash": anchor_hash,
        "read_only": True,
        "creates_authority": False,
        "optional_onchain_anchor_supported": True,
        "authority_boundary": "global_verification_exports_truth_without_creating_runtime_or_production_authority",
    }
    global_bundle_hash = _hash(
        {
            **base,
            "registry": payload,
            "federated_certificate": federation,
            "cross_network_anchors": [anchor.canonical_dict() for anchor in anchors],
        }
    )
    return GlobalVerificationBundle(
        global_bundle_hash=global_bundle_hash,
        registry=payload,
        federated_certificate=federation,
        cross_network_anchors=anchors,
        **base,
    )


def verify_global_verification_bundle(
    bundle: GlobalVerificationBundle | dict[str, Any] | None = None,
) -> dict[str, object]:
    payload = (
        build_global_verification_bundle().canonical_dict()
        if bundle is None
        else bundle.canonical_dict()
        if isinstance(bundle, GlobalVerificationBundle)
        else bundle
    )
    registry = payload.get("registry")
    federation = payload.get("federated_certificate")
    anchors = payload.get("cross_network_anchors")
    registry_verification = (
        verify_registry_payload(registry) if isinstance(registry, dict) else {"verified": False}
    )
    federation_verification = (
        verify_federated_trust_certificate(federation)
        if isinstance(federation, dict)
        else {"verified": False}
    )
    anchor_verification = _verify_cross_network_anchors(
        anchors if isinstance(anchors, list) else [],
        str(payload.get("registry_hash", "")),
        str(payload.get("anchor_hash", "")),
    )
    bundle_hash_valid = _bundle_hash_valid(payload)
    verified = all(
        (
            payload.get("classification") == "LEVEL_15_GLOBAL_PUBLIC_VERIFICATION_LAYER",
            payload.get("level") == "LEVEL_15",
            payload.get("read_only") is True,
            payload.get("creates_authority") is False,
            payload.get("authority_boundary") == "global_verification_exports_truth_without_creating_runtime_or_production_authority",
            registry_verification.get("verified") is True,
            federation_verification.get("verified") is True,
            anchor_verification["verified"],
            bundle_hash_valid,
        )
    )
    return {
        "verified": verified,
        "classification": payload.get("classification"),
        "level": payload.get("level"),
        "status": payload.get("status"),
        "registry_hash": payload.get("registry_hash"),
        "global_bundle_hash": payload.get("global_bundle_hash"),
        "bundle_hash_valid": bundle_hash_valid,
        "registry": registry_verification,
        "federation": federation_verification,
        "cross_network": anchor_verification,
        "guarantees": {
            "truth_independent_of_origin_system": verified,
            "cross_network_interoperable": anchor_verification["verified"],
            "global_public_verification_available": verified,
            "optional_onchain_anchoring_supported": payload.get("optional_onchain_anchor_supported") is True,
            "no_fake_feature_can_exist": registry_verification.get("no_fake_feature_can_exist") is True,
            "no_incomplete_feature_can_appear": registry_verification.get("no_incomplete_feature_can_appear") is True,
            "no_unverifiable_claim_can_be_exported": registry_verification.get("no_unverifiable_claim_can_be_exported") is True,
            "no_production_state_can_be_falsely_implied": registry_verification.get("no_production_state_can_be_falsely_implied") is True,
        },
    }


def write_global_verification_snapshot(
    bundle: GlobalVerificationBundle | None = None,
    *,
    version: str = "v1",
) -> Path:
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    path = REPORT_ROOT / f"{version}.json"
    selected = bundle or build_global_verification_bundle()
    path.write_text(
        json.dumps(selected.canonical_dict(), indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
    return path


def _build_anchor(network: InteroperabilityNetwork, registry_hash: str) -> CrossNetworkAnchor:
    receipt = ChainReceipt(
        tx_hash=f"global-{network.network_id}-{registry_hash[:16]}",
        network=network.network_id,
        block_number=0,
        explorer_url=None,
        status="runtime_safe_fallback",
        chain_id=network.chain_id,
        chain_name=network.name,
        proof_hash=registry_hash,
        authority="global_public_verification_anchor",
        source="global_verification.deterministic_anchor",
        meta={
            "protocol": network.protocol,
            "anchoring_mode": network.anchoring_mode,
            "optional_onchain": network.anchoring_mode == "optional_onchain",
            "truth_independent_of_origin_system": True,
        },
    )
    return CrossNetworkAnchor(
        network=network,
        receipt=receipt,
        receipt_hash=_hash(receipt.canonical_dict()),
        optional_onchain=True,
    )


def _verify_cross_network_anchors(
    anchors: list[dict[str, Any]],
    registry_hash: str,
    expected_anchor_hash: str,
) -> dict[str, object]:
    unique_networks: set[str] = set()
    valid_count = 0
    for anchor in anchors:
        receipt = anchor.get("receipt", {})
        network = anchor.get("network", {})
        receipt_hash = anchor.get("receipt_hash")
        network_id = network.get("network_id") if isinstance(network, dict) else None
        if isinstance(network_id, str):
            unique_networks.add(network_id)
        if (
            isinstance(receipt, dict)
            and receipt.get("proof_hash") == registry_hash
            and receipt_hash == _hash(receipt)
            and receipt.get("status") in {"live", "runtime_safe_fallback"}
        ):
            valid_count += 1
    computed_anchor_hash = _hash(anchors)
    verified = (
        len(unique_networks) >= 2
        and valid_count == len(anchors)
        and len(anchors) >= 2
        and computed_anchor_hash == expected_anchor_hash
    )
    return {
        "verified": verified,
        "network_count": len(unique_networks),
        "anchor_count": len(anchors),
        "valid_anchor_count": valid_count,
        "anchor_hash_valid": computed_anchor_hash == expected_anchor_hash,
        "optional_onchain_anchor_present": any(
            isinstance(anchor.get("network"), dict)
            and anchor["network"].get("anchoring_mode") == "optional_onchain"
            for anchor in anchors
        ),
        "networks": sorted(unique_networks),
    }


def _bundle_hash_valid(payload: dict[str, Any]) -> bool:
    expected = payload.get("global_bundle_hash")
    if not isinstance(expected, str):
        return False
    recomputed = _hash(
        {
            "classification": payload.get("classification"),
            "level": payload.get("level"),
            "status": payload.get("status"),
            "registry_hash": payload.get("registry_hash"),
            "federation_hash": payload.get("federation_hash"),
            "anchor_hash": payload.get("anchor_hash"),
            "read_only": payload.get("read_only"),
            "creates_authority": payload.get("creates_authority"),
            "optional_onchain_anchor_supported": payload.get("optional_onchain_anchor_supported"),
            "authority_boundary": payload.get("authority_boundary"),
            "registry": payload.get("registry"),
            "federated_certificate": payload.get("federated_certificate"),
            "cross_network_anchors": payload.get("cross_network_anchors"),
        }
    )
    return recomputed == expected


__all__ = [
    "CrossNetworkAnchor",
    "GlobalVerificationBundle",
    "InteroperabilityNetwork",
    "build_global_verification_bundle",
    "default_interoperability_networks",
    "verify_global_verification_bundle",
    "write_global_verification_snapshot",
]
