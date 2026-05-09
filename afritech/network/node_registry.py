"""ritech/network/node_registry.py

Node Registry
=============

Manages membership of nodes in the AfriTech distributed network.

Responsibilities:
- Register and track nodes
- Ensure identity integrity
- Maintain node state (active, inactive, unhealthy)
- Provide node discovery for routing and consensus
"""

from __future__ import annotations

from typing import Dict, List, Optional
from datetime import datetime

from network.node_identity import NodeIdentity


# -----------------------------------------------------------------
# REGISTRY ERROR
# -----------------------------------------------------------------

class NodeRegistryError(Exception):
    pass


# -----------------------------------------------------------------
# NODE STATE
# -----------------------------------------------------------------

class NodeState:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    UNHEALTHY = "UNHEALTHY"


# -----------------------------------------------------------------
# NODE RECORD
# -----------------------------------------------------------------

class NodeRecord:

    def __init__(self, identity: NodeIdentity):
        self.identity = identity
        self.state = NodeState.ACTIVE
        self.last_seen = datetime.utcnow().isoformat() + "Z"
        self.failures = 0

    # -------------------------------------------------------------
    # UPDATE HEALTH
    # -------------------------------------------------------------

    def mark_seen(self):
        self.last_seen = datetime.utcnow().isoformat() + "Z"
        self.state = NodeState.ACTIVE
        self.failures = 0

    def mark_failure(self):
        self.failures += 1

        if self.failures >= 3:
            self.state = NodeState.UNHEALTHY

    def deactivate(self):
        self.state = NodeState.INACTIVE

    # -------------------------------------------------------------
    # EXPORT
    # -------------------------------------------------------------

    def to_dict(self):
        return {
            "node": self.identity.to_dict(),
            "state": self.state,
            "last_seen": self.last_seen,
            "failures": self.failures,
        }


# -----------------------------------------------------------------
# NODE REGISTRY
# -----------------------------------------------------------------

class NodeRegistry:

    def __init__(self):
        self.nodes: Dict[str, NodeRecord] = {}

    # -----------------------------------------------------------------
    # REGISTER NODE
    # -----------------------------------------------------------------

    def register(self, identity: NodeIdentity) -> None:

        if not isinstance(identity, NodeIdentity):
            raise NodeRegistryError("Invalid NodeIdentity")

        if not identity.verify():
            raise NodeRegistryError("Node identity integrity check failed")

        node_id = identity.node_id

        if node_id in self.nodes:
            # update existing
            self.nodes[node_id].mark_seen()
        else:
            self.nodes[node_id] = NodeRecord(identity)

    # -----------------------------------------------------------------
    # REMOVE NODE
    # -----------------------------------------------------------------

    def remove(self, node_id: str) -> None:

        if node_id in self.nodes:
            del self.nodes[node_id]

    # -----------------------------------------------------------------
    # GET NODE
    # -----------------------------------------------------------------

    def get(self, node_id: str) -> Optional[NodeRecord]:
        return self.nodes.get(node_id)

    # -----------------------------------------------------------------
    # LIST NODES
    # -----------------------------------------------------------------

    def list_all(self) -> List[NodeRecord]:
        return list(self.nodes.values())

    def list_active(self) -> List[NodeRecord]:
        return [
            n for n in self.nodes.values()
            if n.state == NodeState.ACTIVE
        ]

    def list_unhealthy(self) -> List[NodeRecord]:
        return [
            n for n in self.nodes.values()
            if n.state == NodeState.UNHEALTHY
        ]

    # -----------------------------------------------------------------
    # HEALTH MANAGEMENT
    # -----------------------------------------------------------------

    def mark_seen(self, node_id: str) -> None:
        node = self.get(node_id)
        if node:
            node.mark_seen()

    def mark_failure(self, node_id: str) -> None:
        node = self.get(node_id)
        if node:
            node.mark_failure()

    def deactivate(self, node_id: str) -> None:
        node = self.get(node_id)
        if node:
            node.deactivate()

    # -----------------------------------------------------------------
    # CONSENSUS INPUT (IMPORTANT)
    # -----------------------------------------------------------------

    def get_consensus_nodes(self):
        """
        Returns active nodes for consensus participation
        """
        return self.list_active()

    # -----------------------------------------------------------------
    # METRICS
    # -----------------------------------------------------------------

    def stats(self) -> Dict[str, int]:
        return {
            "total": len(self.nodes),
            "active": len(self.list_active()),
            "unhealthy": len(self.list_unhealthy()),
        }

    # -----------------------------------------------------------------
    # EXPORT
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, List[dict]]:
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()]
        }

    # -----------------------------------------------------------------
    # STRING
    # -----------------------------------------------------------------

    def __repr__(self):
        return f"<NodeRegistry total={len(self.nodes)} active={len(self.list_active())}>"
