"""Public architecture proof and partner demo endpoints."""

from __future__ import annotations

import os
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.architecture.anchor_indexer import (
    ANCHOR_EVENT_SUBSCRIBER,
    ANCHOR_STREAM_HUB,
    build_anchor_detail,
    build_anchor_index_snapshot,
    build_anchor_stream_replay,
    build_anchor_stream_snapshot,
    build_blockchain_architecture_map,
    build_evidence_consistency_policy,
    build_evidence_operational_semantics,
    build_governed_evidence_protocol,
    build_etherscan_contract_verification_report,
    build_cross_network_anchor_reconciliation,
    build_mainnet_promotion_gate,
    remember_publication,
    render_anchor_dashboard_html,
)
from afritech.architecture.blockchain_anchor import (
    BlockchainAnchorStore,
    build_chain_promotion_plan,
    publish_architecture_anchor_contract_with_profile,
    publish_architecture_anchor_with_profile,
)
from afritech.architecture.integrity_proof import (
    build_architecture_integrity_proof,
    build_partner_demo_payload,
)
from afritech.governance.adr_anchor import (
    anchor_adr_to_chain,
    build_adr_contract_link_packet,
    build_adr_anchor_preview,
    hash_adr_artifact,
)
from afritech.ops_dashboard import build_system_integrity_dashboard


LOGGER = logging.getLogger(__name__)


def _json_object(payload: dict[str, Any]) -> dict[str, Any]:
    encoded = jsonable_encoder(payload)
    if not isinstance(encoded, dict):
        raise RuntimeError("architecture payload must encode to JSON object")
    return encoded


def _error_payload(exc: Exception) -> dict[str, Any]:
    return _json_object(
        {
            "status": "generation_failed",
            "classification": "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF",
            "runtime_boundary_status": "UNKNOWN",
            "authority_boundary": (
                "architecture proof generation failed safely; replay and governed "
                "execution remain the authority"
            ),
            "proof": None,
            "error": {
                "code": "ARCHITECTURE_PROOF_GENERATION_FAILED",
                "type": type(exc).__name__,
                "message": str(exc),
            },
        }
    )


def _public_architecture_proof_payload() -> dict[str, Any]:
    proof = build_architecture_integrity_proof().canonical_dict()
    return _json_object(
        {
            "status": "generated",
            "classification": "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF",
            "proof_id": proof.get("proof_id"),
            "runtime_boundary_status": proof.get("runtime_boundary_status"),
            "authority_boundary": proof.get("authority_boundary"),
            "proof": proof,
        }
    )


def _safe_proof_payload() -> dict[str, Any]:
    try:
        return _public_architecture_proof_payload()
    except Exception as exc:
        LOGGER.exception("architecture proof generation failed")
        return _error_payload(exc)


def _proof() -> dict[str, Any]:
    return build_architecture_integrity_proof().canonical_dict()


def build_architecture_proof_router() -> APIRouter:
    router = APIRouter(tags=["architecture-proof"])
    blockchain_store = BlockchainAnchorStore()

    @router.get("/public/architecture/health")
    def architecture_proof_health() -> dict[str, Any]:
        try:
            proof = _proof()
        except Exception as exc:
            LOGGER.exception("architecture proof health failed")
            return _error_payload(exc)

        return _json_object(
            {
                "status": "ready",
                "classification": "CONTROLLED_PUBLIC_ARCHITECTURE_PROOF",
                "runtime_boundary_status": proof.get("runtime_boundary_status"),
                "anchor_id": proof.get("anchor_commitment", {}).get("anchor_id"),
                "authority_boundary": proof.get("authority_boundary"),
            }
        )

    @router.get("/public/architecture/proof")
    def public_architecture_proof() -> dict[str, Any]:
        return _safe_proof_payload()

    @router.get("/public/architecture/chain/networks")
    def public_chain_networks() -> dict[str, Any]:
        proof = _proof()

        return _json_object(
            {
                "classification": "PUBLIC_CHAIN_PROMOTION_PLAN",
                "status": "READY",
                "anchor_id": proof.get("verification_packet", {}).get("anchor_id"),
                "promotion": build_chain_promotion_plan(),
                "authority_boundary": proof.get("authority_boundary"),
            }
        )

    @router.get("/public/architecture/chain/{anchor_id}")
    def public_chain_receipt(anchor_id: str) -> dict[str, Any]:
        proof = _proof()
        expected_anchor_id = proof.get("verification_packet", {}).get("anchor_id")

        if expected_anchor_id != anchor_id:
            return _json_object(
                {
                    "classification": "CONTROLLED_PUBLIC_CHAIN_RECEIPT",
                    "status": "NOT_FOUND",
                    "anchor_id": anchor_id,
                    "authority_boundary": proof.get("authority_boundary"),
                }
            )

        return _json_object(
            {
                "classification": "CONTROLLED_PUBLIC_CHAIN_RECEIPT",
                "status": "READY",
                "anchor_id": anchor_id,
                "chain_receipt": proof.get("public_chain_receipt", {}),
                "authority_boundary": proof.get("authority_boundary"),
            }
        )

    @router.post("/v1/architecture/anchor/blockchain")
    def publish_architecture_anchor(
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        proof = _proof()

        try:
            profile_name = str(payload.get("profile", "sepolia"))
            anchor_id = str(proof.get("verification_packet", {}).get("anchor_id"))
            publication_id = str(proof.get("publication_envelope", {}).get("publication_id"))
            mode = str(payload.get("mode", "raw_transaction")).strip().lower()

            if mode in {"contract", "smart_contract", "architecture_anchor"}:
                publication = publish_architecture_anchor_contract_with_profile(
                    anchor_id=anchor_id,
                    publication_id=publication_id,
                    proof_hash=str(proof.get("proof_hash")),
                    profile_name=profile_name,
                    require_live=True,
                )
            else:
                publication = publish_architecture_anchor_with_profile(
                    anchor_id=anchor_id,
                    publication_id=publication_id,
                    signed_tx_hex=str(payload["signed_tx_hex"]),
                    profile_name=profile_name,
                    rpc_url=payload.get("rpc_url"),
                    contract_address=str(
                        payload.get(
                            "contract_address",
                            "0x0000000000000000000000000000000000000000",
                        )
                    ),
                    chain_name=payload.get("chain_name"),
                    network=payload.get("network"),
                    chain_id=payload.get("chain_id"),
                    explorer_base_url=payload.get("explorer_base_url"),
                )

        except KeyError as exc:
            raise HTTPException(status_code=400, detail=f"missing field: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        blockchain_store.remember(publication)
        index_record = remember_publication(publication, source="api.publish_architecture_anchor")

        return _json_object(
            {
                "classification": "BLOCKCHAIN_ARCHITECTURE_ANCHOR_PUBLICATION",
                "proof_id": proof.get("proof_id"),
                "anchor_id": proof.get("verification_packet", {}).get("anchor_id"),
                "profile": profile_name,
                "mode": getattr(publication, "anchor_mode", "raw_transaction"),
                "publication": publication.canonical_dict(),
                "index_record": index_record.canonical_dict(),
                "etherscan": build_etherscan_contract_verification_report(
                    profile_name=profile_name,
                ),
                "authority_boundary": proof.get("authority_boundary"),
            }
        )

    @router.get("/public/architecture/anchors")
    def public_anchor_index() -> dict[str, Any]:
        return _json_object(build_anchor_index_snapshot())

    @router.get("/public/architecture/anchors/status")
    def public_anchor_status() -> dict[str, Any]:
        profile_name = os.getenv("AFRITECH_CHAIN_MODE", "sepolia")
        return _json_object(
            {
                "classification": "BLOCKCHAIN_ANCHOR_STATUS",
                "status": "READY",
                "auto_publish_on_proof": (
                    os.getenv("AFRITECH_CHAIN_AUTO_PUBLISH_ON_PROOF", "false").lower()
                    == "true"
                ),
                "index": build_anchor_index_snapshot(),
                "stream": build_anchor_stream_snapshot(),
                "etherscan": build_etherscan_contract_verification_report(
                    profile_name=profile_name,
                ),
                "authority_boundary": (
                    "auto_anchor_records_publication_only_and_does_not_create_authority"
                ),
            }
        )

    @router.get("/public/architecture/anchors/dashboard", response_class=HTMLResponse)
    def public_anchor_dashboard() -> str:
        return render_anchor_dashboard_html()

    @router.get("/public/architecture/anchors/explorer", response_class=HTMLResponse)
    def public_anchor_explorer() -> str:
        return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AfriTech Anchor Explorer | NovaTech</title>
    <style>
      body { margin: 0; font-family: Inter, Arial, sans-serif; background: #f4f7fb; color: #142033; }
      main { max-width: 980px; margin: 0 auto; padding: 32px 20px 56px; }
      .panel { background: #fff; border: 1px solid #d8e0ea; border-radius: 8px; padding: 18px; margin-top: 16px; }
      a { color: #185aa8; text-decoration: none; }
      code { background: #eef3f7; padding: 2px 6px; border-radius: 4px; }
    </style>
  </head>
  <body>
    <main>
      <h1>AfriTech Anchor Explorer</h1>
      <p>NovaTech public architecture anchor surface</p>
      <p>External anchor explorer app and public trust surfaces for anchored publications, live stream events, and ADR hashes.</p>
      <div class="panel">
        <div><a href="/public/architecture/anchors/dashboard">Anchor dashboard</a></div>
        <div><a href="/public/architecture/anchors/stream/ws">WebSocket stream</a></div>
        <div><a href="/public/architecture/anchors/stream/replay">Stream replay</a></div>
        <div><a href="/public/architecture/anchors/reconciliation">Cross-network reconciliation</a></div>
        <div><a href="/public/architecture/evidence/policy">Evidence consistency policy</a></div>
        <div><a href="/public/architecture/evidence/semantics">Evidence operational semantics</a></div>
        <div><a href="/public/architecture/evidence/protocol">Governed evidence protocol</a></div>
        <div><a href="/public/architecture/anchors/mainnet-promotion-gate">Mainnet promotion gate</a></div>
        <div><a href="/public/architecture/adr/ADR-0045/hash">ADR hash preview</a></div>
        <div><a href="/public/architecture/adr/ADR-0045/contract-link">ADR contract link</a></div>
        <div><code>ws://&lt;host&gt;/public/architecture/anchors/stream/ws</code></div>
      </div>
    </main>
  </body>
</html>"""

    @router.get("/public/architecture/anchors/stream/status")
    def public_anchor_stream_status() -> dict[str, Any]:
        return _json_object(build_anchor_stream_snapshot())

    @router.get("/public/architecture/anchors/stream/replay")
    def public_anchor_stream_replay(after_sequence: int = 0, limit: int = 50) -> dict[str, Any]:
        return _json_object(
            build_anchor_stream_replay(after_sequence=after_sequence, limit=limit)
        )

    @router.post("/public/architecture/anchors/stream/poll")
    def public_anchor_stream_poll(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        results = ANCHOR_EVENT_SUBSCRIBER.sync_all()
        return _json_object(
            {
                "classification": "BLOCKCHAIN_ANCHOR_EVENT_STREAM_POLL",
                "status": "READY",
                "results": results,
                "index": build_anchor_index_snapshot(),
                "authority_boundary": "polling_indexes_events_only",
            }
        )

    @router.websocket("/public/architecture/anchors/stream/ws")
    async def public_anchor_stream_websocket(websocket: WebSocket) -> None:
        await websocket.accept()
        client = websocket
        ANCHOR_STREAM_HUB.subscribe(client)
        try:
            await websocket.send_json(
                {
                    "classification": "BLOCKCHAIN_ANCHOR_STREAM_SOCKET",
                    "status": "CONNECTED",
                    "stream": build_anchor_stream_snapshot(),
                    "index": build_anchor_index_snapshot(),
                    "authority_boundary": "websocket_stream_is_read_only_and_indexing_only",
                }
            )
            while True:
                message = await websocket.receive_text()
                if message.strip().lower() in {"ping", "status"}:
                    await websocket.send_json(
                        {
                            "classification": "BLOCKCHAIN_ANCHOR_STREAM_SOCKET",
                            "status": "READY",
                            "stream": build_anchor_stream_snapshot(),
                            "index": build_anchor_index_snapshot(),
                            "authority_boundary": "websocket_stream_is_read_only_and_indexing_only",
                        }
                    )
                elif message.strip().lower().startswith("replay"):
                    parts = message.strip().split(":", 1)
                    after_sequence = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 0
                    await websocket.send_json(
                        build_anchor_stream_replay(after_sequence=after_sequence)
                    )
        except WebSocketDisconnect:
            pass
        finally:
            ANCHOR_STREAM_HUB.unsubscribe(client)

    @router.get("/public/architecture/anchors/verification")
    def public_anchor_verification_report() -> dict[str, Any]:
        profile_name = os.getenv("AFRITECH_CHAIN_MODE", "sepolia")
        return _json_object(
            {
                **build_etherscan_contract_verification_report(profile_name=profile_name),
                "architecture_map": "/public/architecture/blockchain/map",
                "anchor_dashboard": "/public/architecture/anchors/dashboard",
                "anchor_stream": "/public/architecture/anchors/stream/status",
                "anchor_abi": "/public/architecture/anchors/verification/abi",
                "anchor_source": "/public/architecture/anchors/verification/source",
            }
        )

    @router.get("/public/architecture/anchors/verification/abi")
    def public_anchor_verification_abi() -> dict[str, Any]:
        from afritech.chain.contracts.architecture_anchor_abi import ARCHITECTURE_ANCHOR_ABI

        return _json_object(
            {
                "classification": "ETHERSCAN_CONTRACT_ABI",
                "status": "READY",
                "contract_name": "ArchitectureAnchor",
                "abi": ARCHITECTURE_ANCHOR_ABI,
                "authority_boundary": "abi_is_public_reference_only",
            }
        )

    @router.get("/public/architecture/anchors/verification/source")
    def public_anchor_verification_source() -> dict[str, Any]:
        from pathlib import Path

        source_path = Path(__file__).resolve().parents[2] / "afritech/contracts/ArchitectureAnchor.sol"
        source = source_path.read_text(encoding="utf-8")
        return _json_object(
            {
                "classification": "ETHERSCAN_CONTRACT_SOURCE",
                "status": "READY",
                "contract_name": "ArchitectureAnchor",
                "source_path": "afritech/contracts/ArchitectureAnchor.sol",
                "source": source,
                "authority_boundary": "source_is_public_reference_only",
            }
        )

    @router.get("/public/architecture/anchors/reconciliation")
    def public_anchor_reconciliation() -> dict[str, Any]:
        return _json_object(build_cross_network_anchor_reconciliation())

    @router.get("/public/architecture/anchors/reconciliation/resolution")
    def public_anchor_reconciliation_resolution() -> dict[str, Any]:
        reconciliation = build_cross_network_anchor_reconciliation()
        return _json_object(
            {
                "classification": "BLOCKCHAIN_ANCHOR_RECONCILIATION_RESOLUTION",
                "status": "READY",
                "entries": [
                    {
                        "proof_hash": entry["proof_hash"],
                        "reconciliation_status": entry["reconciliation_status"],
                        "conflicts": entry["conflicts"],
                        "resolution_strategy": entry["resolution_strategy"],
                        "mainnet_blocking": entry["mainnet_blocking"],
                    }
                    for entry in reconciliation["entries"]
                ],
                "resolution_strategies": reconciliation["resolution_strategies"],
                "authority_boundary": "resolution_semantics_are_governance_guidance_not_truth",
            }
        )

    @router.get("/public/architecture/anchors/mainnet-promotion-gate")
    def public_anchor_mainnet_promotion_gate() -> dict[str, Any]:
        return _json_object(build_mainnet_promotion_gate())

    @router.get("/public/architecture/anchors/{anchor_id}")
    def public_anchor_detail(anchor_id: str) -> dict[str, Any]:
        return _json_object(build_anchor_detail(anchor_id))

    @router.get("/public/architecture/evidence/policy")
    def public_evidence_consistency_policy() -> dict[str, Any]:
        return _json_object(build_evidence_consistency_policy())

    @router.get("/public/architecture/evidence/semantics")
    def public_evidence_operational_semantics() -> dict[str, Any]:
        return _json_object(build_evidence_operational_semantics())

    @router.get("/public/architecture/evidence/protocol")
    def public_governed_evidence_protocol() -> dict[str, Any]:
        return _json_object(build_governed_evidence_protocol())

    @router.get("/public/architecture/blockchain/map")
    def public_blockchain_architecture_map() -> dict[str, Any]:
        return _json_object(build_blockchain_architecture_map())

    @router.get("/public/architecture/adr/{adr_id}/hash")
    def public_adr_hash(adr_id: str) -> dict[str, Any]:
        return _json_object(hash_adr_artifact(adr_id))

    @router.get("/public/architecture/adr/{adr_id}/preview")
    def public_adr_preview(adr_id: str) -> dict[str, Any]:
        return _json_object(build_adr_anchor_preview(adr_id))

    @router.get("/public/architecture/adr/{adr_id}/contract-link")
    def public_adr_contract_link(adr_id: str, profile: str = "sepolia") -> dict[str, Any]:
        return _json_object(build_adr_contract_link_packet(adr_id, profile_name=profile))

    @router.post("/v1/governance/adr/{adr_id}/anchor")
    def publish_adr_anchor(
        adr_id: str,
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "VERIFIER")),
    ) -> dict[str, Any]:
        profile_name = str(payload.get("profile", "sepolia"))
        require_live = bool(payload.get("require_live", False))
        record = anchor_adr_to_chain(adr_id, profile_name=profile_name, require_live=require_live)
        return _json_object(
            {
                "classification": "ADR_ANCHOR_PUBLICATION",
                "status": "READY",
                "record": record.canonical_dict(),
                "authority_boundary": "adr_publication_is_evidence_only",
            }
        )

    @router.get("/public/trust/dashboard")
    def public_trust_dashboard() -> dict[str, Any]:
        proof = _proof()
        latest = blockchain_store.latest()
        indexed_latest = build_anchor_index_snapshot().get("latest")
        public_chain_receipt = proof.get("public_chain_receipt", {})
        live_publication = (
            None
            if latest is None and indexed_latest is None
            else (
                latest.canonical_dict()
                if latest is not None
                else indexed_latest
            )
        )

        return _json_object(
            {
                "classification": "PUBLIC_TRUST_DASHBOARD",
                "status": "READY",
                "authority_boundary": proof.get("authority_boundary"),
                "headline": "NovaTech public trust dashboard",
                "network": public_chain_receipt.get("network", "papc-testnet"),
                "integrity": {
                    "runtime_boundary_status": proof.get("runtime_boundary_status"),
                    "proof_id": proof.get("proof_id"),
                    "anchor_id": proof.get("anchor_commitment", {}).get("anchor_id"),
                    "publication_id": proof.get("publication_envelope", {}).get("publication_id"),
                    "verification_status": proof.get("verification_packet", {}).get(
                        "verification_status"
                    ),
                },
                "chain": {
                    "deterministic_receipt": public_chain_receipt,
                    "live_publication": live_publication,
                    "promotion": build_chain_promotion_plan(),
                },
                "anchors": {
                    "index": build_anchor_index_snapshot(),
                    "verification": build_etherscan_contract_verification_report(
                        profile_name=public_chain_receipt.get("network", "sepolia"),
                    ),
                    "stream": build_anchor_stream_snapshot(),
                    "reconciliation": build_cross_network_anchor_reconciliation(),
                    "evidence_policy": build_evidence_consistency_policy(),
                    "operational_semantics": build_evidence_operational_semantics(),
                    "governed_protocol": build_governed_evidence_protocol(),
                    "mainnet_gate": build_mainnet_promotion_gate(),
                    "dashboard": "/public/architecture/anchors/dashboard",
                    "explorer": "/public/architecture/anchors/explorer",
                    "map": "/public/architecture/blockchain/map",
                },
                "distribution": {
                    "verifier_cli": "afritech-verify",
                    "partner_session_cli": "afritech-verify-session",
                },
                "surfaces": [
                    {"label": "Architecture proof", "path": "/public/architecture/proof"},
                    {
                        "label": "Chain receipt",
                        "path": (
                            "/public/architecture/chain/"
                            f"{proof.get('verification_packet', {}).get('anchor_id')}"
                        ),
                    },
                    {
                        "label": "Chain networks",
                        "path": "/public/architecture/chain/networks",
                    },
                    {
                        "label": "Anchor dashboard",
                        "path": "/public/architecture/anchors/dashboard",
                    },
                    {
                        "label": "Anchor stream",
                        "path": "/public/architecture/anchors/stream/ws",
                    },
                    {
                        "label": "Anchor status",
                        "path": "/public/architecture/anchors/status",
                    },
                    {
                        "label": "Cross-network reconciliation",
                        "path": "/public/architecture/anchors/reconciliation",
                    },
                    {
                        "label": "Reconciliation resolution",
                        "path": "/public/architecture/anchors/reconciliation/resolution",
                    },
                    {
                        "label": "Evidence consistency policy",
                        "path": "/public/architecture/evidence/policy",
                    },
                    {
                        "label": "Evidence operational semantics",
                        "path": "/public/architecture/evidence/semantics",
                    },
                    {
                        "label": "Governed evidence protocol",
                        "path": "/public/architecture/evidence/protocol",
                    },
                    {
                        "label": "Mainnet promotion gate",
                        "path": "/public/architecture/anchors/mainnet-promotion-gate",
                    },
                    {
                        "label": "Etherscan verification",
                        "path": "/public/architecture/anchors/verification",
                    },
                    {
                        "label": "Anchor explorer",
                        "path": "/public/architecture/anchors/explorer",
                    },
                    {
                        "label": "ADR hash preview",
                        "path": "/public/architecture/adr/ADR-0045/hash",
                    },
                    {
                        "label": "Blockchain map",
                        "path": "/public/architecture/blockchain/map",
                    },
                    {
                        "label": "Public verification",
                        "path": (
                            "/public/verify/"
                            f"{proof.get('verification_packet', {}).get('anchor_id')}"
                        ),
                    },
                    {
                        "label": "System integrity demo",
                        "path": "/public/demo/system-integrity",
                    },
                ],
            }
        )

    @router.get("/public/demo/system-integrity")
    def public_demo() -> dict[str, Any]:
        return _json_object(build_partner_demo_payload())

    @router.get("/v1/system/integrity/dashboard")
    def system_dashboard(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER", "PARTNER")),
    ) -> dict[str, Any]:
        return _json_object(build_system_integrity_dashboard())

    return router


__all__ = ["build_architecture_proof_router"]
