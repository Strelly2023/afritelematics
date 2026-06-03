"""
AfriTech Dependency Graph

PURPOSE:
--------
Tracks and resolves dependencies between events/workflows.

Responsibilities:
- register dependencies
- determine execution readiness
- maintain dependency relationships
- support DAG-style orchestration

CRITICAL LAW:
-------------
Dependency Graph MAY:
- track dependencies
- determine execution order

Dependency Graph may NOT:
- modify events
- execute workflows
- introduce non-determinism
"""

# ============================================================
# ✅ DEPENDENCY GRAPH CLASS
# ============================================================

class DependencyGraph:
    """
    Manages event dependencies using a Directed Acyclic Graph (DAG)-like structure.
    """

    def __init__(self):
        # event_id → list of dependencies
        self.graph = {}

        # dependency → dependents (reverse lookup)
        self.reverse_graph = {}

    # ========================================================
    # ✅ ADD DEPENDENCY
    # ========================================================

    def add_dependency(self, event_id: str, depends_on: str):
        """
        Register that event_id depends on depends_on.
        """

        if not event_id or not depends_on:
            raise ValueError("Invalid dependency input")

        self.graph.setdefault(event_id, []).append(depends_on)
        self.reverse_graph.setdefault(depends_on, []).append(event_id)

    # ========================================================
    # ✅ BULK ADD
    # ========================================================

    def add_dependencies(self, event_id: str, dependencies: list):
        """
        Add multiple dependencies at once.
        """

        if not isinstance(dependencies, list):
            raise TypeError("Dependencies must be a list")

        for dep in dependencies:
            self.add_dependency(event_id, dep)

    # ========================================================
    # ✅ GET DEPENDENCIES
    # ========================================================

    def get_dependencies(self, event_id: str):
        """
        Returns dependencies of an event.
        """

        return list(self.graph.get(event_id, []))

    # ========================================================
    # ✅ GET DEPENDENTS
    # ========================================================

    def get_dependents(self, event_id: str):
        """
        Returns events that depend on the given event.
        """

        return list(self.reverse_graph.get(event_id, []))

    # ========================================================
    # ✅ READINESS CHECK
    # ========================================================

    def is_ready(self, event_id: str, completed_events: set):
        """
        Determines if an event is ready for execution.

        Ready when ALL dependencies are completed.
        """

        dependencies = self.get_dependencies(event_id)

        return all(dep in completed_events for dep in dependencies)

    # ========================================================
    # ✅ READY EVENTS BATCH
    # ========================================================

    def get_ready_events(self, completed_events: set):
        """
        Returns all events ready for execution.
        """

        ready = []

        for event_id in self.graph.keys():
            if self.is_ready(event_id, completed_events):
                ready.append(event_id)

        return ready

    # ========================================================
    # ✅ CYCLE DETECTION (CRITICAL)
    # ============================================================

    def detect_cycle(self):
        """
        Detects cycles in dependency graph.

        Returns:
            True if cycle exists
        """

        visited = set()
        recursion_stack = set()

        def visit(node):
            if node in recursion_stack:
                return True

            if node in visited:
                return False

            visited.add(node)
            recursion_stack.add(node)

            for neighbor in self.graph.get(node, []):
                if visit(neighbor):
                    return True

            recursion_stack.remove(node)
            return False

        for node in self.graph:
            if visit(node):
                return True

        return False

    # ========================================================
    # ✅ TOPOLOGICAL SORT
    # ============================================================

    def topological_sort(self):
        """
        Returns execution order based on dependencies.

        Raises exception if cycle exists.
        """

        if self.detect_cycle():
            raise Exception("[DEPENDENCY ERROR] Cycle detected")

        visited = set()
        stack = []

        def visit(node):
            if node in visited:
                return

            visited.add(node)

            for dep in self.graph.get(node, []):
                visit(dep)

            stack.append(node)

        for node in self.graph:
            visit(node)

        return stack[::-1]

    # ========================================================
    # ✅ REMOVE EVENT
    # ============================================================

    def remove_event(self, event_id: str):
        """
        Removes event and its dependencies from graph.
        """

        # Remove from main graph
        self.graph.pop(event_id, None)

        # Remove from reverse graph
        self.reverse_graph.pop(event_id, None)

        # Clean references
        for deps in self.graph.values():
            if event_id in deps:
                deps.remove(event_id)

        for deps in self.reverse_graph.values():
            if event_id in deps:
                deps.remove(event_id)

    # ========================================================
    # ✅ CLEAR GRAPH
    # ============================================================

    def clear(self):
        """
        Removes all dependencies.
        """

        self.graph.clear()
        self.reverse_graph.clear()

    # ========================================================
    # ✅ VALIDATION
    # ============================================================

    def validate(self):
        """
        Validates internal structure consistency.
        """

        for node, deps in self.graph.items():
            if not isinstance(deps, list):
                raise Exception("[DEPENDENCY ERROR] Invalid structure")

        return True

    # ========================================================
    # ✅ TRACE / DEBUG
    # ============================================================

    def trace(self):
        """
        Returns full graph structure (debugging).
        """

        return {
            "graph": dict(self.graph),
            "reverse_graph": dict(self.reverse_graph),
        }