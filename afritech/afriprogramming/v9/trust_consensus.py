from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from math import ceil
from typing import Any, Iterable
from uuid import uuid4

from afritech.afriprogramming.assurance.risk_prediction import RiskPredictionService
from afritech.afriprogramming.assurance.trust_fabric import TrustFabricService
from afritech.afriprogramming.persistence import PlatformStore, get_platform_store
from afritech.afriprogramming.v9.schema import ensure_v9_schema


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _stable_json(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _hash(payload: dict[str, Any]) -> str:
    return sha256(_stable_json(payload).encode("utf-8")).hexdigest()


def _trust_weight(trust_score: int, latency_ms: int) -> float:
    trust_component = max(0.0, min(1.0, trust_score / 100.0))
    latency_component = max(0.25, 1.0 - min(latency_ms, 500) / 1000.0)
    return round(trust_component * latency_component, 4)


def _vote_from_peer(peer: dict[str, Any], proposal_hash: str, risk_score: int) -> dict[str, Any]:
    trust_level = str(peer.get("trust_level", "TRUSTED")).upper()
    base_trust = {
        "TRUSTED": 96,
        "VERIFIED": 90,
        "REVIEW": 74,
        "WATCH": 60,
        "BLOCKED": 15,
    }.get(trust_level, 70)
    latency_ms = int(peer.get("latency_ms", 90))
    weight = _trust_weight(base_trust, latency_ms)
    vote = "accept"
    reason = "peer trust and region status acceptable"
    if base_trust < 50 or risk_score >= 70:
        vote = "reject"
        reason = "peer trust or risk threshold not satisfied"
    elif latency_ms >= 300:
        vote = "abstain"
        reason = "latency too high for stable consensus"
    return {
        "peer_organization_id": peer["peer_organization_id"],
        "region_id": peer.get("region_id") or peer.get("node_id") or peer["peer_organization_id"],
        "vote": vote,
        "weight": weight,
        "latency_ms": latency_ms,
        "reason": reason,
        "signature": peer.get("signature", ""),
        "public_key_id": peer.get("public_key_id", ""),
    }


@dataclass(frozen=True)
class ConsensusRound:
    round_id: str
    organization_id: str
    proposal_hash: str
    consensus_hash: str
    quorum_required: int
    yes_votes: int
    no_votes: int
    abstain_votes: int
    weighted_yes: float
    weighted_no: float
    decision: str
    region_count: int
    latency_ms: int
    risk_score: int
    created_at: str


class TrustFabricConsensusService:
    """Deterministic federated trust consensus with replayable outputs."""

    def __init__(
        self,
        repository: PlatformStore | None = None,
        trust_fabric: TrustFabricService | None = None,
        risk_prediction: RiskPredictionService | None = None,
    ) -> None:
        self.repository = repository or get_platform_store()
        self.trust_fabric = trust_fabric or TrustFabricService(self.repository)
        self.risk_prediction = risk_prediction or RiskPredictionService(self.repository)
        ensure_v9_schema(self.repository)

    def evaluate(
        self,
        *,
        organization_id: str,
        proposal: dict[str, Any],
        peer_votes: Iterable[dict[str, Any]] | None = None,
        quorum: int | None = None,
    ) -> dict[str, Any]:
        proposal_hash = _hash(proposal)
        risk_prediction = self.risk_prediction.predict(
            organization_id=organization_id,
            entity_type="organization",
            entity_id=organization_id,
            horizon_days=30,
        )
        topology = self.trust_fabric.decentralized_trust_graph(organization_id)
        if peer_votes is None:
            peer_source = getattr(self.trust_fabric, "peers", None)
            if callable(peer_source):
                peers = list(peer_source(organization_id))
            else:
                peers = [
                    {
                        "peer_organization_id": node.get("organization_id") or node.get("label") or node.get("node_id"),
                        "region_id": node.get("node_id"),
                        "trust_level": "VERIFIED" if int(node.get("trust_score", 0)) >= 80 else "REVIEW",
                        "latency_ms": 120,
                    }
                    for node in topology.get("nodes", [])
                ]
            peer_votes = (
                _vote_from_peer(
                    {
                        **peer,
                        "latency_ms": self._link_latency(peer, topology.get("edges", [])),
                    },
                    proposal_hash,
                    int(risk_prediction["risk_score"]),
                )
                for peer in peers
            )
        votes = [self._normalize_vote(vote, proposal_hash) for vote in peer_votes]
        quorum_required = quorum or max(2, ceil(max(1, len(votes)) / 2))
        yes_votes = [vote for vote in votes if vote["vote"] == "accept"]
        no_votes = [vote for vote in votes if vote["vote"] == "reject"]
        abstain_votes = [vote for vote in votes if vote["vote"] == "abstain"]
        weighted_yes = round(sum(vote["weight"] for vote in yes_votes), 4)
        weighted_no = round(sum(vote["weight"] for vote in no_votes), 4)
        latency_ms = self._average_latency(votes)
        region_count = len({vote["region_id"] for vote in votes})
        decision = "accepted" if len(yes_votes) >= quorum_required and weighted_yes >= weighted_no else "rejected"
        consensus_hash = _hash(
            {
                "organization_id": organization_id,
                "proposal_hash": proposal_hash,
                "quorum_required": quorum_required,
                "yes_votes": len(yes_votes),
                "no_votes": len(no_votes),
                "abstain_votes": len(abstain_votes),
                "weighted_yes": weighted_yes,
                "weighted_no": weighted_no,
                "decision": decision,
                "region_count": region_count,
                "latency_ms": latency_ms,
                "risk_score": int(risk_prediction["risk_score"]),
            }
        )
        round_id = f"consensus-{uuid4().hex[:12]}"
        round_record = {
            "round_id": round_id,
            "organization_id": organization_id,
            "proposal_hash": proposal_hash,
            "proposal": proposal,
            "quorum_required": quorum_required,
            "yes_votes": len(yes_votes),
            "no_votes": len(no_votes),
            "abstain_votes": len(abstain_votes),
            "weighted_yes": weighted_yes,
            "weighted_no": weighted_no,
            "decision": decision,
            "consensus_hash": consensus_hash,
            "region_count": region_count,
            "latency_ms": latency_ms,
            "risk_score": int(risk_prediction["risk_score"]),
            "created_at": _now(),
        }
        self._store_round(round_record)
        for vote in votes:
            self._store_vote(round_id, organization_id, vote)
        return {
            "consensus_round": round_record,
            "votes": votes,
            "proposal": proposal,
            "proposal_hash": proposal_hash,
            "decision": decision,
            "risk_prediction": risk_prediction,
            "topology": topology,
        }

    def latest_round(self, organization_id: str | None = None) -> dict[str, Any] | None:
        query = "SELECT * FROM trust_consensus_rounds"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT 1"
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            row = conn.execute(query, params).fetchone()
        if row is None:
            return None
        return self._row_to_round(row)

    def rounds(self, organization_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = "SELECT * FROM trust_consensus_rounds"
        params: list[Any] = []
        if organization_id is not None:
            query += " WHERE organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_round(row) for row in rows]

    def votes(self, round_id: str | None = None, organization_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = "SELECT * FROM trust_consensus_votes WHERE 1 = 1"
        params: list[Any] = []
        if round_id is not None:
            query += " AND round_id = ?"
            params.append(round_id)
        if organization_id is not None:
            query += " AND organization_id = ?"
            params.append(organization_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            rows = conn.execute(query, params).fetchall()
        return [
            {
                "vote_id": row["vote_id"],
                "round_id": row["round_id"],
                "organization_id": row["organization_id"],
                "peer_organization_id": row["peer_organization_id"],
                "region_id": row["region_id"],
                "vote": row["vote"],
                "weight": float(row["weight"]),
                "signature": row["signature"],
                "public_key_id": row["public_key_id"],
                "reason": row["reason"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def _row_to_round(self, row: Any) -> dict[str, Any]:
        import json

        return {
            "round_id": row["round_id"],
            "organization_id": row["organization_id"],
            "proposal_hash": row["proposal_hash"],
            "proposal": json.loads(row["proposal_json"]),
            "quorum_required": row["quorum_required"],
            "yes_votes": row["yes_votes"],
            "no_votes": row["no_votes"],
            "abstain_votes": row["abstain_votes"],
            "weighted_yes": float(row["weighted_yes"]),
            "weighted_no": float(row["weighted_no"]),
            "decision": row["decision"],
            "consensus_hash": row["consensus_hash"],
            "region_count": row["region_count"],
            "latency_ms": row["latency_ms"],
            "risk_score": row["risk_score"],
            "created_at": row["created_at"],
        }

    def _store_round(self, round_record: dict[str, Any]) -> None:
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            conn.execute(
                """
                INSERT INTO trust_consensus_rounds (
                    round_id, organization_id, proposal_hash, proposal_json,
                    quorum_required, yes_votes, no_votes, abstain_votes,
                    weighted_yes, weighted_no, decision, consensus_hash,
                    region_count, latency_ms, risk_score, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    round_record["round_id"],
                    round_record["organization_id"],
                    round_record["proposal_hash"],
                    _stable_json(round_record["proposal"]),
                    round_record["quorum_required"],
                    round_record["yes_votes"],
                    round_record["no_votes"],
                    round_record["abstain_votes"],
                    round_record["weighted_yes"],
                    round_record["weighted_no"],
                    round_record["decision"],
                    round_record["consensus_hash"],
                    round_record["region_count"],
                    round_record["latency_ms"],
                    round_record["risk_score"],
                    round_record["created_at"],
                ),
            )
            conn.commit()

    def _store_vote(self, round_id: str, organization_id: str, vote: dict[str, Any]) -> None:
        with self.repository._connect() as conn:  # noqa: SLF001 - repository boundary shim
            conn.execute(
                """
                INSERT INTO trust_consensus_votes (
                    vote_id, round_id, organization_id, peer_organization_id,
                    region_id, vote, weight, signature, public_key_id,
                    reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"vote-{uuid4().hex[:12]}",
                    round_id,
                    organization_id,
                    vote["peer_organization_id"],
                    vote["region_id"],
                    vote["vote"],
                    vote["weight"],
                    vote.get("signature", ""),
                    vote.get("public_key_id", ""),
                    vote["reason"],
                    _now(),
                ),
            )
            conn.commit()

    def _normalize_vote(self, vote: dict[str, Any], proposal_hash: str) -> dict[str, Any]:
        vote_value = str(vote.get("vote", "abstain")).lower()
        if vote_value not in {"accept", "reject", "abstain"}:
            vote_value = "abstain"
        normalized = {
            "peer_organization_id": str(vote.get("peer_organization_id", "peer")),
            "region_id": str(vote.get("region_id", vote.get("peer_organization_id", "region"))),
            "vote": vote_value,
            "weight": float(vote.get("weight", 1.0)),
            "latency_ms": int(vote.get("latency_ms", 0)),
            "reason": str(vote.get("reason", "")) or "peer submitted vote",
            "signature": str(vote.get("signature", "")),
            "public_key_id": str(vote.get("public_key_id", "")),
            "proposal_hash": proposal_hash,
        }
        normalized["weight"] = round(max(0.0, min(1.0, normalized["weight"])), 4)
        return normalized

    def _average_latency(self, votes: list[dict[str, Any]]) -> int:
        if not votes:
            return 0
        latencies = [int(vote.get("latency_ms", 120)) for vote in votes]
        return int(round(sum(latencies) / len(latencies)))

    def _link_latency(self, peer: dict[str, Any], edges: list[dict[str, Any]]) -> int:
        peer_id = str(peer.get("peer_organization_id"))
        matching = [
            edge
            for edge in edges
            if peer_id in {
                str(edge.get("source_node_id", "")),
                str(edge.get("target_node_id", "")),
            }
        ]
        if not matching:
            return 120
        return int(round(sum(int(edge.get("metadata", {}).get("latency_ms", 120)) for edge in matching) / len(matching)))


__all__ = ["ConsensusRound", "TrustFabricConsensusService"]
