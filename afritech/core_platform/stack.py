"""Protocol + rails + apps stack composition for NovaTech/NovaPay/NovaRide.

This module deliberately separates:

- protocol: cryptographic verification, receipts, light clients, replay safety
- rails: payment, settlement, eventing, and trust-node operational paths
- apps: product-facing surfaces that consume the protocol and rails

The stack is descriptive, deterministic, and safe to expose via API.
It does not claim public production readiness by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from afritech.core_platform.cbdc import cbdc_status
from afritech.core_platform.cryptographic_consensus import (
    build_cryptographic_consensus_status,
)
from afritech.core_platform.event_bus import build_event_bus_status
from afritech.core_platform.hash_domains import PROTOCOL_HASH_VERSION, SIGNED_MESSAGE_PREFIX
from afritech.core_platform.payments.mobile_money import mobile_money_catalog
from afritech.core_platform.payments.providers import payid_status
from afritech.core_platform.settlement import build_settlement_status
from afritech.core_platform.signing import signing_key_ready, signing_key_status
from afritech.core_platform.threshold_bls import BLS_AVAILABLE
from afritech.core_platform.trust_node import build_trust_node_network_status


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class StackSurface:
    key: str
    label: str
    layer: str
    kind: str
    status: str
    ready: bool
    path: str | None = None
    notes: str | None = None

    def canonical(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "key": self.key,
            "label": self.label,
            "layer": self.layer,
            "kind": self.kind,
            "status": self.status,
            "ready": self.ready,
        }
        if self.path is not None:
            payload["path"] = self.path
        if self.notes is not None:
            payload["notes"] = self.notes
        return payload


@dataclass(frozen=True)
class StackLayer:
    key: str
    label: str
    status: str
    ready: bool
    surfaces: tuple[StackSurface, ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "label": self.label,
            "status": self.status,
            "ready": self.ready,
            "surfaces": [surface.canonical() for surface in self.surfaces],
        }


@dataclass(frozen=True)
class NovaTechStack:
    platform: str
    protocol_version: str
    signed_message_prefix: str
    protocol: StackLayer
    rails: StackLayer
    apps: StackLayer
    ready: bool

    def canonical(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "protocol_version": self.protocol_version,
            "signed_message_prefix": self.signed_message_prefix,
            "ready": self.ready,
            "protocol": self.protocol.canonical(),
            "rails": self.rails.canonical(),
            "apps": self.apps.canonical(),
        }


def _file_exists(*relative_parts: str) -> bool:
    return (REPO_ROOT.joinpath(*relative_parts)).exists()


def _status_label(ready: bool, *, partial: bool = False) -> str:
    if ready:
        return "ready"
    return "available" if partial else "blocked"


def _protocol_layer() -> StackLayer:
    consensus = build_cryptographic_consensus_status()
    signing = signing_key_status()
    protocol_surfaces = (
        StackSurface(
            key="cryptographic_consensus",
            label="Cryptographic consensus",
            layer="protocol",
            kind="verification",
            status="ready" if consensus["cryptographic_consensus_ready"] else "blocked",
            ready=bool(consensus["cryptographic_consensus_ready"]),
            path="afritech/core_platform/cryptographic_consensus.py",
        ),
        StackSurface(
            key="proof_receipts",
            label="Proof receipts",
            layer="protocol",
            kind="verification",
            status="ready" if BLS_AVAILABLE else "available",
            ready=bool(BLS_AVAILABLE),
            path="afritech/core_platform/proof_receipts.py",
            notes="BLS-backed receipt verification when py_ecc is available",
        ),
        StackSurface(
            key="zk_receipts",
            label="ZK receipts",
            layer="protocol",
            kind="verification",
            status=_status_label(True),
            ready=True,
            path="afritech/core_platform/zk_receipts.py",
        ),
        StackSurface(
            key="stateless_verifier",
            label="Stateless verifier",
            layer="protocol",
            kind="verification",
            status=_status_label(True),
            ready=True,
            path="afritech/core_platform/stateless_verifier.py",
        ),
        StackSurface(
            key="cross_chain_light_client",
            label="Cross-chain light client",
            layer="protocol",
            kind="bridge",
            status=_status_label(True),
            ready=True,
            path="afritech/core_platform/cross_chain_light_client.py",
        ),
        StackSurface(
            key="onchain_light_verifier",
            label="On-chain light verifier",
            layer="protocol",
            kind="contract",
            status=_status_label(True),
            ready=True,
            path="afritech/core_platform/onchain_light_verifier.py",
        ),
        StackSurface(
            key="privacy_qr",
            label="Privacy QR envelope",
            layer="protocol",
            kind="transport",
            status=_status_label(True),
            ready=True,
            path="afritech/core_platform/privacy_qr.py",
        ),
        StackSurface(
            key="signature_layer",
            label="Signing key layer",
            layer="protocol",
            kind="signing",
            status="ready" if signing_key_ready() else "blocked",
            ready=bool(signing_key_ready()),
            path="afritech/core_platform/signing.py",
            notes=(
                f"hash_version={PROTOCOL_HASH_VERSION}; "
                f"prefix={SIGNED_MESSAGE_PREFIX}; "
                f"provider={signing.provider}"
            ),
        ),
    )
    ready = all(surface.ready for surface in protocol_surfaces)
    return StackLayer(
        key="protocol",
        label="NovaTrust protocol",
        status="ready" if ready else "blocked",
        ready=ready,
        surfaces=protocol_surfaces,
    )


def _rails_layer() -> StackLayer:
    payid = payid_status()
    mobile_money = mobile_money_catalog()
    cbdc = cbdc_status()
    settlement = build_settlement_status()
    event_bus = build_event_bus_status()
    trust_network = build_trust_node_network_status()
    rails_surfaces = (
        StackSurface(
            key="payid",
            label="PayID rail",
            layer="rails",
            kind="payment",
            status="ready" if payid["ready_for_real_charge"] else "pilot",
            ready=bool(payid["ready_for_real_charge"]),
            path="afritech/core_platform/payments/providers.py",
        ),
        StackSurface(
            key="mobile_money",
            label="Mobile money rail catalog",
            layer="rails",
            kind="payment",
            status="ready",
            ready=True,
            path="afritech/core_platform/payments/mobile_money.py",
            notes=f"{len(mobile_money['countries'])} regulated country corridors",
        ),
        StackSurface(
            key="cbdc",
            label="CBDC adapter",
            layer="rails",
            kind="payment",
            status="ready" if cbdc["ready_for_real_charge"] else "available",
            ready=bool(cbdc["ready_for_real_charge"]),
            path="afritech/core_platform/cbdc.py",
        ),
        StackSurface(
            key="settlement",
            label="Settlement router",
            layer="rails",
            kind="settlement",
            status="ready",
            ready=True,
            path="afritech/core_platform/settlement.py",
            notes=f"default_rails={','.join(sorted(settlement['domestic_rails'].values()))}",
        ),
        StackSurface(
            key="event_bus",
            label="Event bus",
            layer="rails",
            kind="eventing",
            status="ready" if event_bus["event_bus"]["ready"] else "blocked",
            ready=bool(event_bus["event_bus"]["ready"]),
            path="afritech/core_platform/event_bus.py",
        ),
        StackSurface(
            key="trust_node_network",
            label="Trust node network",
            layer="rails",
            kind="network",
            status="ready" if trust_network["distributed_validation_ready"] else "configuration_required",
            ready=bool(trust_network["distributed_validation_ready"]),
            path="afritech/core_platform/trust_node.py",
        ),
    )
    ready = all(surface.ready for surface in rails_surfaces)
    return StackLayer(
        key="rails",
        label="NovaPay rails",
        status="ready" if ready else "blocked",
        ready=ready,
        surfaces=rails_surfaces,
    )


def _apps_layer() -> StackLayer:
    app_surfaces = (
        StackSurface(
            key="novaride_driver_app",
            label="NovaRide Driver",
            layer="apps",
            kind="mobile",
            status="ready" if _file_exists("afriride_system", "mobile", "driver_app", "App.js") else "missing",
            ready=_file_exists("afriride_system", "mobile", "driver_app", "App.js"),
            path="afriride_system/mobile/driver_app/App.js",
        ),
        StackSurface(
            key="novaride_passenger_app",
            label="NovaRide Passenger",
            layer="apps",
            kind="mobile",
            status="ready" if _file_exists("afriride_system", "mobile", "passenger_app", "App.js") else "missing",
            ready=_file_exists("afriride_system", "mobile", "passenger_app", "App.js"),
            path="afriride_system/mobile/passenger_app/App.js",
        ),
        StackSurface(
            key="novaride_operator_app",
            label="NovaRide Operator",
            layer="apps",
            kind="mobile",
            status="ready" if _file_exists("afriride_system", "mobile", "operator_app", "App.js") else "missing",
            ready=_file_exists("afriride_system", "mobile", "operator_app", "App.js"),
            path="afriride_system/mobile/operator_app/App.js",
        ),
        StackSurface(
            key="novaride_flutter_verifier",
            label="NovaRide Flutter verifier",
            layer="apps",
            kind="mobile",
            status="ready" if _file_exists("afriride_system", "flutter", "driver_app", "lib", "screens", "verifier_screen.dart") else "available",
            ready=_file_exists("afriride_system", "flutter", "driver_app", "lib", "screens", "verifier_screen.dart"),
            path="afriride_system/flutter/driver_app/lib/screens/verifier_screen.dart",
        ),
        StackSurface(
            key="novapay_api",
            label="NovaPay API",
            layer="apps",
            kind="backend",
            status="ready",
            ready=True,
            path="afritech/api/core_platform_api.py",
            notes="payment execution, trust replay, proof receipts, and readiness endpoints",
        ),
        StackSurface(
            key="public_trust_explorer",
            label="Public trust explorer",
            layer="apps",
            kind="backend",
            status="ready",
            ready=True,
            path="afritech/api/core_platform_api.py",
        ),
        StackSurface(
            key="protocol_shared_modules",
            label="Shared protocol modules",
            layer="apps",
            kind="shared",
            status="ready" if _file_exists("afriride_system", "mobile", "shared", "verificationLayer.js") else "available",
            ready=_file_exists("afriride_system", "mobile", "shared", "verificationLayer.js"),
            path="afriride_system/mobile/shared/",
            notes="canonicalize / crypto / proof / UI / verifier shared surfaces",
        ),
    )
    ready = all(surface.ready for surface in app_surfaces)
    return StackLayer(
        key="apps",
        label="NovaRide and NovaPay apps",
        status="ready" if ready else "available",
        ready=ready,
        surfaces=app_surfaces,
    )


def build_novatech_stack() -> NovaTechStack:
    protocol = _protocol_layer()
    rails = _rails_layer()
    apps = _apps_layer()
    ready = protocol.ready and rails.ready and apps.ready
    return NovaTechStack(
        platform="NovaTechSol",
        protocol_version=PROTOCOL_HASH_VERSION,
        signed_message_prefix=SIGNED_MESSAGE_PREFIX,
        protocol=protocol,
        rails=rails,
        apps=apps,
        ready=ready,
    )


def build_novatech_stack_readiness() -> dict[str, Any]:
    stack = build_novatech_stack()
    return {
        "platform": stack.platform,
        "ready": stack.ready,
        "protocol_ready": stack.protocol.ready,
        "rails_ready": stack.rails.ready,
        "apps_ready": stack.apps.ready,
        "stack": stack.canonical(),
    }


__all__ = [
    "NovaTechStack",
    "StackLayer",
    "StackSurface",
    "build_novatech_stack",
    "build_novatech_stack_readiness",
]
