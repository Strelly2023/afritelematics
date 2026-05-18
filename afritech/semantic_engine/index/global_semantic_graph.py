from dataclasses import dataclass, field


@dataclass
class GlobalSemanticGraph:
    edges: dict[str, set[str]] = field(default_factory=dict)

    def add_node(self, node: str) -> None:
        self.edges.setdefault(node, set())

    def add_dependency(self, node: str, depends_on: str) -> None:
        self.add_node(node)
        self.add_node(depends_on)
        self.edges[node].add(depends_on)

    def dependencies(self, node: str) -> list[str]:
        return sorted(self.edges.get(node, set()))

    def validate_acyclic(self) -> bool:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visited:
                return
            if node in visiting:
                raise ValueError("semantic_dependency_cycle")
            visiting.add(node)
            for dependency in self.edges.get(node, set()):
                visit(dependency)
            visiting.remove(node)
            visited.add(node)

        for node in sorted(self.edges):
            visit(node)
        return True
