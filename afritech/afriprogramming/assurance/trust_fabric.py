from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any
from urllib import request as urllib_request

from afritech.afriprogramming.assurance.pki import PKIService
from afritech.afriprogramming.persistence import PlatformStore, get_platform_store


def _stable_digest(payload: dict[str, Any]) -> str:
    import json

    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class SignedRequestEnvelope:
    organization_id: str
    peer_organization_id: str
    method: str
    url: str
    headers: dict[str, Any]
    body_hash: str
    signature: str
    public_key: str
    created_at: str
    nonce: str

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "peer_organization_id": self.peer_organization_id,
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "body_hash": self.body_hash,
            "signature": self.signature,
            "public_key": self.public_key,
            "created_at": self.created_at,
            "nonce": self.nonce,
        }


class TrustFabricService:
    def __init__(self, repository: PlatformStore | None = None, pki_service: PKIService | None = None) -> None:
        self.repository = repository or get_platform_store()
        self.pki = pki_service or PKIService(self.repository)

    def register_region(
        self,
        *,
        organization_id: str,
        region_name: str,
        country_code: str,
        provider: str,
        status: str = "active",
    ) -> dict[str, Any]:
        region = self.repository.register_trust_region(
            organization_id=organization_id,
            region_name=region_name,
            country_code=country_code,
            provider=provider,
            status=status,
        )
        self.repository.store_graph_node(
            organization_id=organization_id,
            node_type="region",
            label=region_name,
            trust_score=82 if status == "active" else 40,
            metadata={"country_code": country_code, "provider": provider, "region_id": region["region_id"]},
        )
        return region

    def regions(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_trust_regions(organization_id=organization_id)

    def link_regions(
        self,
        *,
        organization_id: str,
        source_region_id: str,
        target_region_id: str,
        latency_ms: int,
        trust_score: int,
        status: str = "active",
    ) -> dict[str, Any]:
        link = self.repository.link_trust_regions(
            organization_id=organization_id,
            source_region_id=source_region_id,
            target_region_id=target_region_id,
            latency_ms=latency_ms,
            trust_score=trust_score,
            status=status,
        )
        self.repository.store_graph_edge(
            organization_id=organization_id,
            source_node_id=source_region_id,
            target_node_id=target_region_id,
            edge_type="cross_region_link",
            weight=max(0.0, min(1.0, trust_score / 100.0)),
            metadata={"latency_ms": latency_ms, "status": status, "link_id": link["link_id"]},
        )
        return link

    def links(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_trust_region_links(organization_id=organization_id)

    def sign_request(
        self,
        *,
        organization_id: str,
        peer_organization_id: str,
        method: str,
        url: str,
        headers: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        key_family: str = "federation-http",
    ) -> dict[str, Any]:
        payload = {
            "organization_id": organization_id,
            "peer_organization_id": peer_organization_id,
            "method": method.upper(),
            "url": url,
            "headers": headers or {},
            "body_hash": _stable_digest(body or {}),
            "nonce": _stable_digest(
                {
                    "organization_id": organization_id,
                    "peer_organization_id": peer_organization_id,
                    "url": url,
                    "body": body or {},
                }
            )[:24],
        }
        signed = self.pki.sign(organization_id=organization_id, payload=payload, key_family=key_family)
        envelope = SignedRequestEnvelope(
            organization_id=organization_id,
            peer_organization_id=peer_organization_id,
            method=method.upper(),
            url=url,
            headers=headers or {},
            body_hash=payload["body_hash"],
            signature=signed["signature"],
            public_key=signed["public_key"],
            created_at=_now(),
            nonce=payload["nonce"],
        )
        record = self.repository.store_signed_http_request(
            organization_id=organization_id,
            peer_organization_id=peer_organization_id,
            method=envelope.method,
            url=url,
            headers=headers or {},
            body_hash=envelope.body_hash,
            signature=envelope.signature,
            public_key=envelope.public_key,
            verified=True,
        )
        return {
            **record,
            "nonce": envelope.nonce,
            "headers": headers or {},
            "body_hash": envelope.body_hash,
        }

    def verify_request(self, envelope: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "organization_id": envelope.get("organization_id"),
            "peer_organization_id": envelope.get("peer_organization_id"),
            "method": str(envelope.get("method", "")).upper(),
            "url": envelope.get("url"),
            "headers": envelope.get("headers", {}),
            "body_hash": envelope.get("body_hash"),
            "nonce": envelope.get("nonce"),
        }
        public_key = str(envelope.get("public_key", ""))
        signature = str(envelope.get("signature", ""))
        valid = bool(public_key and signature and self.pki.verify(public_key=public_key, payload=payload, signature=signature))
        if valid:
            self.repository.store_signed_http_request(
                organization_id=str(envelope.get("organization_id")),
                peer_organization_id=str(envelope.get("peer_organization_id")),
                method=str(envelope.get("method", "")).upper(),
                url=str(envelope.get("url", "")),
                headers=dict(envelope.get("headers", {})),
                body_hash=str(envelope.get("body_hash", "")),
                signature=signature,
                public_key=public_key,
                verified=True,
            )
        return {
            "valid": valid,
            "organization_id": envelope.get("organization_id"),
            "peer_organization_id": envelope.get("peer_organization_id"),
            "method": envelope.get("method"),
            "url": envelope.get("url"),
        }

    def send_signed_request(
        self,
        *,
        organization_id: str,
        peer_organization_id: str,
        method: str,
        url: str,
        headers: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        envelope = self.sign_request(
            organization_id=organization_id,
            peer_organization_id=peer_organization_id,
            method=method,
            url=url,
            headers=headers,
            body=body,
        )
        req = urllib_request.Request(url=url, method=method.upper())
        for key, value in (headers or {}).items():
            req.add_header(str(key), str(value))
        req.add_header("X-Nova-Organization", organization_id)
        req.add_header("X-Nova-Peer-Organization", peer_organization_id)
        req.add_header("X-Nova-Signature", envelope["signature"])
        req.add_header("X-Nova-Public-Key", envelope["public_key"])
        if body is not None:
            import json

            data = json.dumps(body, sort_keys=True).encode("utf-8")
            req.data = data
            req.add_header("Content-Type", "application/json")
        return {
            "request": envelope,
            "delivery": "prepared",
            "headers": dict(req.header_items()),
        }

    def graph_snapshot(self, organization_id: str | None = None) -> dict[str, Any]:
        nodes = self.repository.list_graph_nodes(organization_id=organization_id)
        edges = self.repository.list_graph_edges(organization_id=organization_id)
        node_index = {node["node_id"]: node for node in nodes}
        centrality = {
            node_id: sum(1 for edge in edges if edge["source_node_id"] == node_id or edge["target_node_id"] == node_id)
            for node_id in node_index
        }
        return {
            "organization_id": organization_id,
            "nodes": nodes,
            "edges": edges,
            "centrality": centrality,
            "decentralized": bool(len(nodes) > 2 and len(edges) >= len(nodes) - 1),
        }

    def decentralized_trust_graph(self, organization_id: str | None = None) -> dict[str, Any]:
        graph = self.graph_snapshot(organization_id=organization_id)
        trust_regions = self.regions(organization_id=organization_id)
        bindings = self.identity_bindings(organization_id=organization_id)
        score = min(100, 20 + len(graph["nodes"]) * 8 + len(graph["edges"]) * 4 + len(trust_regions) * 3 + len(bindings) * 2)
        return {
            **graph,
            "trust_regions": trust_regions,
            "identity_bindings": bindings,
            "graph_score": score,
        }

    def identity_bind(
        self,
        *,
        organization_id: str,
        user_id: str,
        device_id: str,
        human_trust_score: int,
        device_trust_score: int,
        attestation: dict[str, Any],
    ) -> dict[str, Any]:
        signed = self.pki.sign(
            organization_id=organization_id,
            payload=attestation,
            key_family="identity",
        )
        binding = self.repository.bind_identity(
            organization_id=organization_id,
            user_id=user_id,
            device_id=device_id,
            human_trust_score=human_trust_score,
            device_trust_score=device_trust_score,
            attestation_hash=signed["payload_hash"],
            signed_by_key_id=signed["key_id"],
            trust_level="BOUND",
        )
        self.repository.store_graph_node(
            organization_id=organization_id,
            node_type="human",
            label=user_id,
            trust_score=human_trust_score,
            metadata={"binding_id": binding["binding_id"], "device_id": device_id},
        )
        self.repository.store_graph_node(
            organization_id=organization_id,
            node_type="device",
            label=device_id,
            trust_score=device_trust_score,
            metadata={"binding_id": binding["binding_id"], "user_id": user_id},
        )
        self.repository.store_graph_edge(
            organization_id=organization_id,
            source_node_id=f"human:{user_id}",
            target_node_id=f"device:{device_id}",
            edge_type="identity_bound",
            weight=max(0.0, min(1.0, (human_trust_score + device_trust_score) / 200.0)),
            metadata={"binding_id": binding["binding_id"], "attestation_hash": signed["payload_hash"]},
        )
        return binding

    def identity_bindings(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_identity_bindings(organization_id=organization_id)

    def identity_score(self, organization_id: str | None = None, user_id: str | None = None) -> dict[str, Any]:
        bindings = self.identity_bindings(organization_id=organization_id)
        relevant = [binding for binding in bindings if user_id is None or binding["user_id"] == user_id]
        if not relevant:
            return {
                "organization_id": organization_id,
                "user_id": user_id,
                "identity_trust_score": 0,
                "identity_bound": False,
            }
        score = round(
            sum(int(item["human_trust_score"]) * 0.55 + int(item["device_trust_score"]) * 0.45 for item in relevant)
            / len(relevant)
        )
        return {
            "organization_id": organization_id,
            "user_id": user_id,
            "identity_trust_score": int(score),
            "identity_bound": True,
            "bindings": relevant,
        }

    def negotiate(
        self,
        *,
        organization_id: str,
        peer_organization_id: str,
        proposed_terms: dict[str, Any],
        trust_offer: int,
        trust_floor: int,
    ) -> dict[str, Any]:
        request = self.sign_request(
            organization_id=organization_id,
            peer_organization_id=peer_organization_id,
            method="POST",
            url=f"https://{peer_organization_id}/trust/negotiation",
            body=proposed_terms,
            key_family="federation-http",
        )
        session = self.repository.store_negotiation_session(
            organization_id=organization_id,
            peer_organization_id=peer_organization_id,
            proposed_terms=proposed_terms,
            trust_offer=trust_offer,
            trust_floor=trust_floor,
            signed_request=request,
        )
        decision = "accept" if trust_offer >= trust_floor else "counter"
        if decision == "counter":
            session = self.repository.update_negotiation_session(
                negotiation_id=session["negotiation_id"],
                organization_id=organization_id,
                state="countered",
                counter_terms={
                    "required_trust": trust_floor,
                    "proposal": proposed_terms,
                },
            )
        else:
            session = self.repository.update_negotiation_session(
                negotiation_id=session["negotiation_id"],
                organization_id=organization_id,
                state="accepted",
                counter_terms=proposed_terms,
            )
        self.repository.store_negotiation_event(
            organization_id=organization_id,
            negotiation_id=session["negotiation_id"],
            event_type=f"negotiation.{decision}",
            payload={
                "trust_offer": trust_offer,
                "trust_floor": trust_floor,
                "proposal": proposed_terms,
            },
        )
        return {
            "negotiation": session,
            "decision": decision,
            "signed_request": request,
        }

    def negotiation_sessions(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_negotiation_sessions(organization_id=organization_id)

    def negotiation_events(self, organization_id: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list_negotiation_events(organization_id=organization_id)


__all__ = ["SignedRequestEnvelope", "TrustFabricService"]
