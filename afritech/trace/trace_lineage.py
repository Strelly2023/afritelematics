# afritech/trace/trace_lineage.py

"""
AfriTech Trace Lineage Module

Purpose:
Provide causal reasoning utilities over the trace DAG.

Responsibilities:
- compute full dependency lineage (transitive closure)
- compute reverse dependencies (impact analysis)
- validate dependency paths
- extract causal paths
- compute lineage hashes (cryptographic proof binding)
- ensure DAG consistency during traversal

This is the CAUSAL ANALYSIS layer of TRACE.
"""

from __future__ import annotations

from typing import Dict, Any, List, Set
import hashlib

from afritech.trace.trace_hash import canonical_json


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class TraceLineageError(Exception):
    """Trace lineage or causal analysis error"""
    pass


# -----------------------------------------------------------------
# LINEAGE ENGINE
# -----------------------------------------------------------------

class TraceLineage:

    # =============================================================
    # LINEAGE (TRANSITIVE DEPENDENCIES)
    # =============================================================

    @classmethod
    def lineage(cls, trace: Dict[str, Any], index: int) -> List[int]:
        """
        Compute full dependency lineage for an event.

        Returns:
            Sorted list of all upstream dependency indices
            (transitive closure).
        """

        events = cls._get_events(trace)
        cls._validate_index(events, index)

        visited: Set[int] = set()

        def dfs(i: int):
            for dep in events[i].get("depends_on", []):
                if dep not in visited:
                    visited.add(dep)
                    dfs(dep)

        dfs(index)
        return sorted(visited)

    # =============================================================
    # DIRECT DEPENDENCIES
    # =============================================================

    @classmethod
    def direct_dependencies(cls, trace: Dict[str, Any], index: int) -> List[int]:
        """
        Return immediate dependencies of an event.
        """

        events = cls._get_events(trace)
        cls._validate_index(events, index)

        return sorted(events[index].get("depends_on", []))

    # =============================================================
    # REVERSE DEPENDENCIES (IMPACT ANALYSIS)
    # =============================================================

    @classmethod
    def reverse_dependencies(cls, trace: Dict[str, Any], index: int) -> List[int]:
        """
        Find all events that depend (directly or indirectly) on this event.
        """

        events = cls._get_events(trace)
        cls._validate_index(events, index)

        reverse_map = cls._build_reverse_map(events)

        visited: Set[int] = set()

        def dfs(i: int):
            for dependent in reverse_map.get(i, []):
                if dependent not in visited:
                    visited.add(dependent)
                    dfs(dependent)

        dfs(index)
        return sorted(visited)

    # =============================================================
    # BUILD REVERSE DEPENDENCY MAP
    # =============================================================

    @staticmethod
    def _build_reverse_map(events: List[Dict[str, Any]]) -> Dict[int, List[int]]:
        """
        Build reverse dependency map: dep → [dependents].
        """

        reverse: Dict[int, List[int]] = {i: [] for i in range(len(events))}

        for event in events:
            idx = event["index"]
            for dep in event.get("depends_on", []):
                reverse[dep].append(idx)

        return reverse

    # =============================================================
    # DEPENDENCY CHECK
    # =============================================================

    @classmethod
    def is_dependent(cls, trace: Dict[str, Any], src: int, target: int) -> bool:
        """
        Check whether target depends (transitively) on src.
        """

        return src in cls.lineage(trace, target)

    # =============================================================
    # CAUSAL PATH (ONE VALID PATH)
    # =============================================================

    @classmethod
    def find_path(cls, trace: Dict[str, Any], src: int, target: int) -> List[int]:
        """
        Find one valid dependency path from src → target.

        Raises:
            TraceLineageError if no path exists.
        """

        events = cls._get_events(trace)
        cls._validate_index(events, src)
        cls._validate_index(events, target)

        path: List[int] = []

        def dfs(current: int, visited: Set[int]) -> bool:
            if current == src:
                path.append(current)
                return True

            if current in visited:
                return False

            visited.add(current)

            for dep in events[current].get("depends_on", []):
                if dfs(dep, visited):
                    path.append(current)
                    return True

            return False

        if not dfs(target, set()):
            raise TraceLineageError("no_path_found")

        return list(reversed(path))

    # =============================================================
    # LINEAGE HASH (CRYPTOGRAPHIC COMMITMENT)
    # =============================================================

    @classmethod
    def lineage_hash(cls, trace: Dict[str, Any], index: int) -> str:
        """
        Compute cryptographic commitment of an event's lineage.

        This binds:
        - dependency indices
        - upstream event hashes
        """

        events = cls._get_events(trace)
        cls._validate_index(events, index)

        lineage_indices = cls.lineage(trace, index)

        event_hashes = [
            events[i]["event_hash"]
            for i in lineage_indices
        ]

        payload = {
            "lineage": lineage_indices,
            "event_hashes": event_hashes,
        }

        return hashlib.sha256(
            canonical_json(payload).encode("utf-8")
        ).hexdigest()

    # =============================================================
    # SUBGRAPH EXTRACTION
    # =============================================================

    @classmethod
    def extract_subgraph(
        cls,
        trace: Dict[str, Any],
        index: int,
    ) -> List[Dict[str, Any]]:
        """
        Extract subgraph of events in the lineage of index.
        """

        events = cls._get_events(trace)
        lineage_indices = cls.lineage(trace, index)

        return [events[i] for i in lineage_indices]

    # =============================================================
    # ROOT EVENT CHECK
    # =============================================================

    @classmethod
    def is_root_event(cls, trace: Dict[str, Any], index: int) -> bool:
        """
        Check whether an event has no dependencies.
        """

        events = cls._get_events(trace)
        cls._validate_index(events, index)

        return len(events[index].get("depends_on", [])) == 0

    # =============================================================
    # LEAF EVENTS (NO DEPENDENTS)
    # =============================================================

    @classmethod
    def leaf_events(cls, trace: Dict[str, Any]) -> List[int]:
        """
        Return indices of events that no other events depend on.
        """

        events = cls._get_events(trace)
        reverse_map = cls._build_reverse_map(events)

        return sorted(
            idx for idx, dependents in reverse_map.items()
            if not dependents
        )

    # =============================================================
    # HELPERS
    # =============================================================

    @staticmethod
    def _get_events(trace: Dict[str, Any]) -> List[Dict[str, Any]]:
        if "events" not in trace or not isinstance(trace["events"], list):
            raise TraceLineageError("missing_events")
        return trace["events"]

    @staticmethod
    def _validate_index(events: List[Dict[str, Any]], index: int) -> None:
        if not isinstance(index, int) or index < 0 or index >= len(events):
            raise TraceLineageError("invalid_index")

    # =============================================================
    # DEBUG
    # =============================================================

    def __repr__(self) -> str:
        return "<TraceLineage causal-analysis>"