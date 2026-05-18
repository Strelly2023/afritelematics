from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProofNode:
    node_id: str
    proof_hash: str
    expression_hash: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProofDAG:
    nodes: dict[str, ProofNode] = field(default_factory=dict)
    edges: dict[str, set[str]] = field(default_factory=dict)

    def add_proof(self, node: ProofNode, depends_on: list[str] | None = None) -> None:
        self.nodes[node.node_id] = node
        self.edges.setdefault(node.node_id, set()).update(depends_on or [])
        for dependency in depends_on or []:
            self.edges.setdefault(dependency, set())

    def topological_order(self) -> list[str]:
        visited: set[str] = set()
        visiting: set[str] = set()
        ordered: list[str] = []

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            if node_id in visiting:
                raise ValueError("proof_dag_cycle")
            visiting.add(node_id)
            for dependency in sorted(self.edges.get(node_id, set())):
                visit(dependency)
            visiting.remove(node_id)
            visited.add(node_id)
            ordered.append(node_id)

        for node_id in sorted(self.edges):
            visit(node_id)
        return ordered
