"""Compatibility analysis for API endpoint changes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import ApiEndpointDefinition


@dataclass(frozen=True, slots=True)
class ApiCompatibilityResult:
    classification: str
    additions: tuple[str, ...]
    removals: tuple[str, ...]
    request_changes: tuple[str, ...]
    response_changes: tuple[str, ...]
    permission_changes: tuple[str, ...]
    route_changes: tuple[str, ...]
    breaking_changes: tuple[str, ...]


class ApiCompatibilityValidator:
    def classify(
        self,
        current: tuple[ApiEndpointDefinition, ...],
        proposed: tuple[ApiEndpointDefinition, ...],
    ) -> ApiCompatibilityResult:
        current_by_id = {item.endpoint_id: item for item in current}
        proposed_by_id = {item.endpoint_id: item for item in proposed}
        additions = tuple(sorted(set(proposed_by_id) - set(current_by_id)))
        removals = tuple(sorted(set(current_by_id) - set(proposed_by_id)))
        route_changes = []
        permission_changes = []
        request_changes = []
        response_changes = []
        breaking_changes = []
        for endpoint_id in set(current_by_id) & set(proposed_by_id):
            cur = current_by_id[endpoint_id]
            prop = proposed_by_id[endpoint_id]
            if (cur.path, cur.methods) != (prop.path, prop.methods):
                route_changes.append(endpoint_id)
            if cur.required_roles != prop.required_roles or cur.required_permissions != prop.required_permissions:
                permission_changes.append(endpoint_id)
            if cur.request_schema != prop.request_schema:
                request_changes.append(endpoint_id)
            if cur.response_schema != prop.response_schema:
                response_changes.append(endpoint_id)
            if removals or route_changes or permission_changes or request_changes or response_changes:
                breaking_changes.append(endpoint_id)
        classification = "ADDITIVE" if additions and not removals and not breaking_changes else "BREAKING" if breaking_changes or removals else "COMPATIBLE"
        return ApiCompatibilityResult(
            classification=classification,
            additions=additions,
            removals=removals,
            request_changes=tuple(request_changes),
            response_changes=tuple(response_changes),
            permission_changes=tuple(permission_changes),
            route_changes=tuple(route_changes),
            breaking_changes=tuple(breaking_changes),
        )
