"""Deterministic AfriRide route planning.

Routing is a bounded optimization layer. It consumes a declared ride and a
declared map graph, then returns an immutable route plan without mutating ride
state, emitting events, pricing, or reading live traffic.
"""

from __future__ import annotations

import heapq
import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Mapping, Sequence

from ecosystems.afriride.domain.models.canonical_ride import Ride


class RoutingViolation(ValueError):
    """Raised when route inputs are undeclared, invalid, or disconnected."""


@dataclass(frozen=True)
class RoutePlan:
    """Deterministic route output for a ride."""

    ride_id: str
    ride_hash: str
    path: tuple[str, ...]
    distance: float
    estimated_time: float
    cost_basis: str
    graph_hash: str

    def to_canonical_dict(self) -> dict[str, Any]:
        """Return a deterministic JSON-ready route representation."""

        return {
            "cost_basis": self.cost_basis,
            "distance": self.distance,
            "estimated_time": self.estimated_time,
            "graph_hash": self.graph_hash,
            "path": list(self.path),
            "ride_hash": self.ride_hash,
            "ride_id": self.ride_id,
        }

    def canonical_json(self) -> str:
        """Return stable canonical JSON for trace and replay."""

        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    def route_hash(self) -> str:
        """Return a deterministic content hash for the route plan."""

        return sha256(self.canonical_json().encode("utf-8")).hexdigest()


def compute_route(ride: Ride, map_graph: Mapping[str, Any]) -> RoutePlan:
    """Compute the deterministic shortest route for a declared ride and graph."""

    if not isinstance(ride, Ride):
        raise RoutingViolation("ride must be a canonical Ride")

    start = _extract_node_id("ride.pickup_location", ride.pickup_location)
    end = _extract_node_id("ride.dropoff_location", ride.dropoff_location)
    graph = _normalize_graph(map_graph)
    if start not in graph["nodes"]:
        raise RoutingViolation(f"pickup node is not declared in graph: {start}")
    if end not in graph["nodes"]:
        raise RoutingViolation(f"dropoff node is not declared in graph: {end}")

    path, distance, estimated_time = _shortest_path(graph["edges"], start, end)
    return RoutePlan(
        ride_id=ride.id,
        ride_hash=ride.ride_hash(),
        path=path,
        distance=distance,
        estimated_time=estimated_time,
        cost_basis="distance_then_time_then_path",
        graph_hash=_graph_hash(graph),
    )


def canonical_graph_json(map_graph: Mapping[str, Any]) -> str:
    """Return stable canonical JSON for a declared map graph."""

    return json.dumps(
        _normalize_graph(map_graph),
        sort_keys=True,
        separators=(",", ":"),
    )


def _shortest_path(
    edges: Mapping[str, tuple[dict[str, Any], ...]],
    start: str,
    end: str,
) -> tuple[tuple[str, ...], float, float]:
    queue: list[tuple[float, float, tuple[str, ...], str]] = [(0.0, 0.0, (start,), start)]
    best: dict[str, tuple[float, float, tuple[str, ...]]] = {}

    while queue:
        distance, estimated_time, path, node = heapq.heappop(queue)
        current_score = (distance, estimated_time, path)
        if node in best and best[node] <= current_score:
            continue
        best[node] = current_score

        if node == end:
            return path, distance, estimated_time

        for edge in edges.get(node, ()):
            target = edge["to"]
            if target in path:
                continue
            heapq.heappush(
                queue,
                (
                    round(distance + edge["distance"], 9),
                    round(estimated_time + edge["estimated_time"], 9),
                    path + (target,),
                    target,
                ),
            )

    raise RoutingViolation(f"No declared route from {start} to {end}")


def _normalize_graph(map_graph: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(map_graph, Mapping):
        raise RoutingViolation("map_graph must be a declared mapping")

    raw_nodes = map_graph.get("nodes")
    raw_edges = map_graph.get("edges")
    if not isinstance(raw_nodes, Mapping) or not raw_nodes:
        raise RoutingViolation("map_graph.nodes must be a non-empty mapping")
    if not isinstance(raw_edges, Sequence) or isinstance(raw_edges, (str, bytes)):
        raise RoutingViolation("map_graph.edges must be a declared sequence")

    nodes = {str(node_id): _canonicalize(raw_nodes[node_id]) for node_id in sorted(raw_nodes)}
    edge_table: dict[str, list[dict[str, Any]]] = {node_id: [] for node_id in nodes}

    for raw_edge in raw_edges:
        if not isinstance(raw_edge, Mapping):
            raise RoutingViolation("map graph edge must be a declared mapping")
        source = _require_text("edge.from", raw_edge.get("from"))
        target = _require_text("edge.to", raw_edge.get("to"))
        if source not in nodes:
            raise RoutingViolation(f"edge source is not declared: {source}")
        if target not in nodes:
            raise RoutingViolation(f"edge target is not declared: {target}")
        edge_table[source].append(
            {
                "distance": _require_number("edge.distance", raw_edge.get("distance")),
                "estimated_time": _require_number(
                    "edge.estimated_time",
                    raw_edge.get("estimated_time"),
                ),
                "to": target,
            }
        )

    return {
        "edges": {
            source: tuple(
                sorted(
                    edges,
                    key=lambda edge: (
                        edge["distance"],
                        edge["estimated_time"],
                        edge["to"],
                    ),
                )
            )
            for source, edges in sorted(edge_table.items())
        },
        "nodes": nodes,
    }


def _graph_hash(graph: Mapping[str, Any]) -> str:
    return sha256(
        json.dumps(graph, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _extract_node_id(field_name: str, value: Mapping[str, Any]) -> str:
    return _require_text(f"{field_name}.node_id", value.get("node_id"))


def _require_text(field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RoutingViolation(f"{field_name} must be declared as non-empty text")
    return value


def _require_number(field_name: str, value: Any) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        raise RoutingViolation(f"{field_name} must be declared as a non-negative number")
    return round(float(value), 9)


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, tuple):
        return [_canonicalize(item) for item in value]
    if isinstance(value, list):
        return [_canonicalize(item) for item in value]
    return value
