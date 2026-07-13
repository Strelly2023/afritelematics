from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "enterprise-solution"


def _hash_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def default_agent_registry() -> list[dict[str, Any]]:
    return [
        {
            "id": "architect-agent",
            "name": "Architect Agent",
            "specialization": "Architecture",
            "permissions": ["requirements.read", "architecture.create", "graph.read"],
            "tools": ["architecture-studio", "knowledge-graph", "approval-center"],
            "models": ["c4", "ddd", "sequence"],
            "risk_limit": "HIGH",
        },
        {
            "id": "developer-agent",
            "name": "Developer Agent",
            "specialization": "Implementation",
            "permissions": ["code.write", "tests.generate", "api.write"],
            "tools": ["code-studio", "test-studio", "api-studio"],
            "models": ["react", "fastapi", "postgres"],
            "risk_limit": "MEDIUM",
        },
        {
            "id": "qa-agent",
            "name": "QA Agent",
            "specialization": "Quality",
            "permissions": ["tests.generate", "tests.execute", "evidence.write"],
            "tools": ["test-studio", "evidence-service"],
            "models": ["unit", "integration", "e2e"],
            "risk_limit": "MEDIUM",
        },
        {
            "id": "security-agent",
            "name": "Security Agent",
            "specialization": "Security",
            "permissions": ["security.review", "risk.assess", "evidence.write"],
            "tools": ["security-studio", "risk-engine", "approval-center"],
            "models": ["threat-model", "sast", "dependency-scan"],
            "risk_limit": "HIGH",
        },
        {
            "id": "compliance-agent",
            "name": "Compliance Agent",
            "specialization": "Compliance",
            "permissions": ["policy.read", "compliance.review", "approval.route"],
            "tools": ["compliance-studio", "approval-center"],
            "models": ["control-mapping", "regulatory-review"],
            "risk_limit": "HIGH",
        },
        {
            "id": "legal-agent",
            "name": "Legal Agent",
            "specialization": "Legal",
            "permissions": ["contract.read", "legal.review", "approval.route"],
            "tools": ["legal-studio", "approval-center"],
            "models": ["contract-analysis", "risk-spotting"],
            "risk_limit": "HIGH",
        },
        {
            "id": "data-agent",
            "name": "Data Agent",
            "specialization": "Data",
            "permissions": ["data.read", "lineage.read", "graph.read"],
            "tools": ["data-architecture", "data-lineage", "knowledge-graph"],
            "models": ["schema", "lineage", "feature-store"],
            "risk_limit": "HIGH",
        },
    ]


def select_agent_team(request_text: str, risk_level: str = "medium") -> list[str]:
    normalized = request_text.lower()
    team = ["architect-agent", "developer-agent", "qa-agent"]
    if any(term in normalized for term in ("security", "auth", "payment", "production", "deploy", "incident", "risk")):
        team.append("security-agent")
    if any(term in normalized for term in ("compliance", "privacy", "regulat", "policy", "consent", "retention")):
        team.append("compliance-agent")
    if any(term in normalized for term in ("legal", "contract", "agreement", "license", "nda")):
        team.append("legal-agent")
    if any(term in normalized for term in ("data", "model", "dataset", "feature", "warehouse", "lakehouse", "analytics")):
        team.append("data-agent")
    if risk_level.lower() in {"high", "critical"} and "security-agent" not in team:
        team.append("security-agent")
    if risk_level.lower() in {"high", "critical"} and "compliance-agent" not in team:
        team.append("compliance-agent")
    return list(dict.fromkeys(team))


def build_solution_package(request: dict[str, Any], registry: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    request_text = str(request.get("request") or request.get("title") or "Enterprise solution")
    title = str(request.get("title") or request_text[:80] or "Enterprise solution")
    solution_id = str(request.get("solution_id") or _new_id("solution"))
    approval_type = str(request.get("approval_type") or "solution_review")
    risk_level = str(request.get("risk_level") or "medium").upper()
    registry = registry or default_agent_registry()
    team_ids = select_agent_team(request_text, risk_level)
    team = [agent for agent in registry if agent["id"] in team_ids]
    created_at = _now()
    solution = {
        "id": solution_id,
        "slug": _slug(title),
        "title": title,
        "request": request_text,
        "project_id": str(request.get("project_id") or ""),
        "workflow_id": str(request.get("workflow_id") or ""),
        "status": "review",
        "risk_level": risk_level,
        "version": str(request.get("version") or "1"),
        "created_at": created_at,
        "updated_at": created_at,
    }
    approval = build_approval_object(
        solution=solution,
        approval_type=approval_type,
        approver=str(request.get("approver") or "NovaTech Governance"),
        comments=list(request.get("comments") or []),
        execution_enabled=bool(request.get("execution_enabled", False)),
    )
    knowledge = build_knowledge_entry(
        solution=solution,
        approval=approval,
        previous_version=str(request.get("previous_version") or ""),
        evidence_ids=list(request.get("evidence_ids") or []),
    )
    events = []
    for sequence, event_type, payload in (
        (1, "solution.created", {"solution_id": solution_id, "title": title}),
        (2, "agent.team.selected", {"solution_id": solution_id, "agents": [item["id"] for item in team]}),
        (3, "approval.requested", {"solution_id": solution_id, "approval_id": approval["id"]}),
        (4, "knowledge.entry.promoted", {"solution_id": solution_id, "knowledge_id": knowledge["id"]}),
    ):
        events.append(
            build_event_record(
                aggregate_id=solution_id,
                aggregate_type="solution",
                event_type=event_type,
                sequence=sequence,
                payload=payload,
            )
        )
    return {
        "solution": solution,
        "agent_team": team,
        "approval": approval,
        "knowledge_entry": knowledge,
        "events": events,
        "review_workspace": {
            "request": request_text,
            "layers": [
                "Main Workspace",
                "AI Assistant",
                "Collaboration",
                "Activity",
                "Smart Command Bar",
            ],
        },
    }


def build_approval_object(
    *,
    solution: dict[str, Any],
    approval_type: str,
    approver: str,
    comments: list[str] | None = None,
    execution_enabled: bool = False,
) -> dict[str, Any]:
    created_at = _now()
    comments = list(comments or [])
    risk_level = str(solution.get("risk_level") or "medium").upper()
    status = "APPROVED" if not execution_enabled and risk_level in {"LOW", "MEDIUM"} else "REVIEWED"
    return {
        "id": _new_id("approval"),
        "solution_id": str(solution["id"]),
        "approval_type": approval_type,
        "status": status,
        "risk_level": risk_level,
        "approver": approver,
        "comments": comments,
        "approved_at": created_at if status == "APPROVED" else "",
        "version": int(solution.get("version") or 1),
        "knowledge_created": status == "APPROVED",
        "execution_enabled": execution_enabled and status == "APPROVED",
        "created_at": created_at,
        "updated_at": created_at,
    }


def build_knowledge_entry(
    *,
    solution: dict[str, Any],
    approval: dict[str, Any],
    previous_version: str = "",
    evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    created_at = _now()
    evidence_ids = list(evidence_ids or [])
    approved = str(approval.get("status") or "").upper() == "APPROVED"
    return {
        "id": _new_id("knowledge"),
        "solution_id": str(solution["id"]),
        "approval_id": str(approval["id"]),
        "title": str(solution.get("title") or "Enterprise solution"),
        "type": "approved-solution",
        "version": int(solution.get("version") or 1),
        "status": "APPROVED" if approved else "REVIEWED",
        "approved": approved,
        "previous_version": previous_version,
        "links": [value for value in (approval.get("solution_id"), previous_version) if value],
        "evidence_ids": evidence_ids,
        "hash": _hash_payload(
            {
                "solution_id": solution["id"],
                "approval_id": approval["id"],
                "version": solution.get("version") or 1,
                "evidence_ids": evidence_ids,
            }
        ),
        "created_at": created_at,
        "updated_at": created_at,
    }


def build_event_record(
    *,
    aggregate_id: str,
    aggregate_type: str,
    event_type: str,
    sequence: int,
    payload: dict[str, Any],
    actor: str = "NovaAI",
) -> dict[str, Any]:
    return {
        "event_id": _new_id("event"),
        "aggregate_id": aggregate_id,
        "aggregate_type": aggregate_type,
        "event_type": event_type,
        "sequence": sequence,
        "payload": dict(payload),
        "actor": actor,
        "occurred_at": _now(),
    }


def replay_events(
    events: list[dict[str, Any]],
    projector: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any] | None],
    *,
    initial_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = dict(initial_state or {})
    ordered = sorted(
        events,
        key=lambda item: (
            str(item.get("aggregate_id") or item.get("correlation_id") or item.get("workflow_id") or ""),
            int(item.get("sequence") or 0),
            str(item.get("event_id") or ""),
        ),
    )
    for event in ordered:
        next_state = projector(state, event)
        if next_state is not None:
            state = next_state
    return state


def knowledge_projection(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes: dict[str, dict[str, Any]] = {}

    def projector(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
        payload = event.get("payload") or event.get("data") or {}
        if event.get("event_type") == "knowledge.entry.promoted":
            node_id = str(payload.get("knowledge_id") or event["event_id"])
            nodes[node_id] = {
                "id": node_id,
                "solution_id": str(
                    payload.get("solution_id")
                    or event.get("correlation_id")
                    or event.get("workflow_id")
                    or event["event_id"]
                ),
                "approval_id": str(payload.get("approval_id") or ""),
                "version": int(payload.get("version") or 1),
                "status": "APPROVED",
                "links": list(payload.get("links") or []),
            }
        elif event.get("event_type") == "approval.requested":
            state["last_approval"] = payload.get("approval_id")
        return state

    replay_events(events, projector, initial_state={})
    return list(nodes.values())
