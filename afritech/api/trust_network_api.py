"""FastAPI trust registry and verification network surface."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.crypto.multi_party_verification import (
    VerificationWitness,
    build_multi_party_verification_record,
)
from afritech.partner_verification import build_partner_verification_packet
from afritech.partner_verification import PartnerVerificationStore
from afritech.standards_dependency import (
    StandardsDependencyStore,
    build_standard_conformance_profile,
    register_protocol_dependency,
)
from afritech.trust_network import (
    TrustRegistryStore,
    build_trust_network_verification,
    publish_trust_registry_entry,
)


def build_trust_network_router(
    store: TrustRegistryStore | None = None,
    dependency_store: StandardsDependencyStore | None = None,
    verification_store: PartnerVerificationStore | None = None,
) -> APIRouter:
    router = APIRouter(tags=["trust-network"])
    registry_store = store or TrustRegistryStore()
    dependency_store = dependency_store or StandardsDependencyStore()
    verification_store = verification_store or PartnerVerificationStore()

    @router.get("/v1/trust/standards/profile")
    def get_standard_profile() -> dict[str, Any]:
        return build_standard_conformance_profile().canonical_dict()

    @router.post("/v1/trust/dependents/register")
    def register_dependent(
        payload: dict[str, Any],
        _: object = Depends(require_roles("PARTNER", "OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            record = register_protocol_dependency(
                dependent_id=str(payload["dependent_id"]),
                organization=str(payload["organization"]),
                use_case=str(payload["use_case"]),
                protocol_version=str(payload.get("protocol_version", "1.0.0")),
            )
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"missing field: {exc.args[0]}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        dependency_store.register(record)
        return record.canonical_dict()

    @router.get("/v1/trust/dependents")
    def list_dependents(
        _: object = Depends(require_roles("PARTNER", "OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        return {
            "dependents": [entry.canonical_dict() for entry in dependency_store.list_records()]
        }

    @router.get("/v1/trust/registry")
    def list_registry(
        _: object = Depends(require_roles("PARTNER", "OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        return {"entries": [entry.canonical_dict() for entry in registry_store.list_entries()]}

    @router.post("/v1/trust/registry/publish")
    def publish_registry(
        payload: dict[str, Any],
        _: object = Depends(require_roles("PARTNER", "OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            packet = build_partner_verification_packet(
                tenant_id=str(payload["tenant_id"]),
                region_id=str(payload["region_id"]),
                trace_hash=str(payload["trace_hash"]),
                replay_hash=str(payload["replay_hash"]),
                receipt_hash=str(payload["receipt_hash"]),
                authority_hash=str(payload["authority_hash"]),
                execution_fingerprint=str(payload["execution_fingerprint"]),
                publication_target=str(payload["publication_target"]),
                network=str(payload.get("network", "external-ledger-testnet")),
                external_reference=payload.get("external_reference"),
            )
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"missing field: {exc.args[0]}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        verification_store.remember(packet)
        entry = publish_trust_registry_entry(packet, dependency_store.list_records())
        registry_store.publish(entry)
        return entry.canonical_dict()

    @router.post("/v1/trust/network/verify")
    def verify_network(
        payload: dict[str, Any],
        _: object = Depends(require_roles("PARTNER", "OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        try:
            packet = build_partner_verification_packet(
                tenant_id=str(payload["tenant_id"]),
                region_id=str(payload["region_id"]),
                trace_hash=str(payload["trace_hash"]),
                replay_hash=str(payload["replay_hash"]),
                receipt_hash=str(payload["receipt_hash"]),
                authority_hash=str(payload["authority_hash"]),
                execution_fingerprint=str(payload["execution_fingerprint"]),
                publication_target=str(payload["publication_target"]),
                network=str(payload.get("network", "external-ledger-testnet")),
                external_reference=payload.get("external_reference"),
            )
            raw_witnesses = payload["witnesses"]
            witnesses = tuple(
                VerificationWitness(
                    verifier_id=str(item["verifier_id"]),
                    organization=str(item["organization"]),
                    decision=str(item["decision"]),
                    evidence_hash=str(item["evidence_hash"]),
                )
                for item in raw_witnesses
            )
            record = build_multi_party_verification_record(
                packet,
                witnesses,
                quorum=int(payload.get("quorum", 2)),
            )
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"missing field: {exc.args[0]}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        verification_store.remember(packet)
        dependents = dependency_store.list_records()
        network = build_trust_network_verification(record, dependents)
        return {
            "registry_entry": publish_trust_registry_entry(packet, dependents).canonical_dict(),
            "verification_network": network.canonical_dict(),
            "witness_manifest_hash": record.witness_manifest_hash,
        }

    return router


__all__ = ["build_trust_network_router"]
