from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any


@dataclass(frozen=True)
class FederationNode:
    node_id: str
    region: str
    role: str
    trust_weight: int

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "region": self.region,
            "role": self.role,
            "trust_weight": self.trust_weight,
        }


class NovaScriptFederation:
    def __init__(self) -> None:
        self._nodes = {
            "novascript-primary": FederationNode("novascript-primary", "global", "coordinator", 50),
            "novascript-policy": FederationNode("novascript-policy", "governance", "policy_verifier", 25),
            "novascript-repository": FederationNode("novascript-repository", "engineering", "repository_intelligence", 25),
        }
        self._organizations: dict[str, dict[str, Any]] = {
            "novatrust-root": {
                "organization_id": "novatrust-root",
                "trust_domain": "root",
                "public_profile_hash": sha256(b"novatrust-root").hexdigest(),
                "trust_score": 100,
            }
        }
        self._exchanges: list[dict[str, Any]] = []

    def register_organization(self, *, organization_id: str, trust_domain: str, trust_score: int) -> dict[str, Any]:
        profile = {
            "organization_id": organization_id,
            "trust_domain": trust_domain,
            "public_profile_hash": sha256(f"{organization_id}:{trust_domain}:{trust_score}".encode()).hexdigest(),
            "trust_score": max(0, min(100, int(trust_score))),
        }
        self._organizations[organization_id] = profile
        return profile

    def register_node(self, *, node_id: str, region: str, role: str, trust_weight: int = 10) -> dict[str, Any]:
        normalized = node_id.strip()
        self._nodes[normalized] = FederationNode(
            node_id=normalized,
            region=region.strip() or "unknown",
            role=role.strip() or "worker",
            trust_weight=max(0, min(100, int(trust_weight))),
        )
        return self._nodes[normalized].canonical_dict()

    def status(self) -> dict[str, Any]:
        nodes = [node.canonical_dict() for node in self._nodes.values()]
        return {
            "mode": "multi_node_novascript",
            "node_count": len(nodes),
            "quorum_weight": 67,
            "nodes": sorted(nodes, key=lambda item: item["node_id"]),
            "organization_count": len(self._organizations),
        }

    def consensus(self, *, project_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        payload_hash = sha256(str(sorted(payload.items())).encode("utf-8")).hexdigest()
        votes = []
        accepted_weight = 0
        for node in sorted(self._nodes.values(), key=lambda item: item.node_id):
            vote_hash = sha256(f"{node.node_id}:{project_id}:{payload_hash}".encode("utf-8")).hexdigest()
            accepted = node.trust_weight > 0
            accepted_weight += node.trust_weight if accepted else 0
            votes.append(
                {
                    "node_id": node.node_id,
                    "accepted": accepted,
                    "trust_weight": node.trust_weight,
                    "vote_hash": vote_hash,
                }
            )
        return {
            "federation_id": "fed-" + sha256(f"{project_id}:{payload_hash}".encode("utf-8")).hexdigest()[:12],
            "project_id": project_id,
            "payload_hash": payload_hash,
            "accepted_weight": accepted_weight,
            "quorum_weight": 67,
            "verified": accepted_weight >= 67,
            "votes": votes,
        }

    def trust_exchange(
        self,
        *,
        issuer_org: str,
        subject_org: str,
        receipt_hash: str,
        trust_score: int,
    ) -> dict[str, Any]:
        if issuer_org not in self._organizations:
            self.register_organization(organization_id=issuer_org, trust_domain="tenant", trust_score=80)
        if subject_org not in self._organizations:
            self.register_organization(organization_id=subject_org, trust_domain="tenant", trust_score=80)
        issuer = self._organizations[issuer_org]
        subject = self._organizations[subject_org]
        exchange_hash = sha256(
            f"{issuer['public_profile_hash']}:{subject['public_profile_hash']}:{receipt_hash}:{trust_score}".encode()
        ).hexdigest()
        exchange = {
            "mode": "cross_organization_trust_exchange",
            "exchange_id": "trustx-" + exchange_hash[:12],
            "issuer_org": issuer_org,
            "subject_org": subject_org,
            "receipt_hash": receipt_hash,
            "trust_score": max(0, min(100, int(trust_score))),
            "verified": issuer["trust_score"] >= 60 and subject["trust_score"] >= 60,
            "exchange_hash": exchange_hash,
        }
        self._exchanges.append(exchange)
        return exchange

    def trust_graph(self) -> dict[str, Any]:
        nodes = [
            {
                "id": org["organization_id"],
                "type": "organization",
                "trust_domain": org["trust_domain"],
                "trust_score": org["trust_score"],
            }
            for org in sorted(self._organizations.values(), key=lambda item: item["organization_id"])
        ]
        edges = [
            {
                "id": exchange["exchange_id"],
                "type": "trust_exchange",
                "source": exchange["issuer_org"],
                "target": exchange["subject_org"],
                "verified": exchange["verified"],
                "trust_score": exchange["trust_score"],
            }
            for exchange in self._exchanges[-25:]
        ]
        graph_hash = sha256(f"{len(nodes)}:{len(edges)}:{sorted(edge['id'] for edge in edges)}".encode()).hexdigest()
        return {
            "mode": "federated_trust_graph",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "graph_hash": graph_hash,
        }


_DEFAULT_FEDERATION = NovaScriptFederation()


def get_novascript_federation() -> NovaScriptFederation:
    return _DEFAULT_FEDERATION
