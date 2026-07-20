from __future__ import annotations

import csv
import hashlib
import io
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from .platform import NovaCodeProPlatform, _new_id, _now


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(obj: Any) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


def _text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _tenant(record: dict[str, Any]) -> str:
    return str(record.get("tenant_id") or "")


def _tenant_scope(records: Iterable[dict[str, Any]], tenant_id: str) -> list[dict[str, Any]]:
    return [record for record in records if not tenant_id or _tenant(record) == tenant_id]


def _status(record: dict[str, Any]) -> str:
    return str(record.get("status") or "")


def _version(record: dict[str, Any]) -> int:
    try:
        return int(record.get("version") or 1)
    except Exception:  # noqa: BLE001
        return 1


REQUIRED_BLUEPRINT_SECTIONS = (
    "vision",
    "mission",
    "business_problem",
    "market",
    "users_and_personas",
    "value_proposition",
    "capabilities",
    "functional_requirements",
    "non_functional_requirements",
    "architecture",
    "data_model",
    "integrations",
    "security",
    "privacy",
    "compliance",
    "user_experience",
    "delivery_strategy",
    "deployment_model",
    "operations",
    "observability",
    "resilience",
    "release_strategy",
    "commercial_assumptions",
    "risks",
    "exclusions",
    "dependencies",
    "acceptance_criteria",
)


LIFECYCLE_TEMPLATE_PHASES = (
    "Strategy and Research",
    "Planning and Analysis",
    "Requirements Definition",
    "UI/UX Design",
    "Architecture and Data Design",
    "Development",
    "Integration",
    "Quality Engineering",
    "Security and Compliance",
    "Deployment Readiness",
    "Controlled Pilot",
    "Public Pilot",
    "Production Readiness Review",
    "General Availability",
    "Operations and Continuous Improvement",
    "Retirement",
)


WORKFLOW_STATES = (
    "Draft",
    "Published",
    "Scheduled",
    "Running",
    "Waiting",
    "Blocked",
    "Paused",
    "Compensating",
    "Completed",
    "Failed",
    "Cancelled",
    "Expired",
)


LIFECYCLE_INSTANCE_STATES = (
    "Not Started",
    "Ready",
    "In Progress",
    "Generated",
    "Under Review",
    "Changes Required",
    "Approved",
    "Blocked",
    "Completed",
    "Waived",
    "Archived",
)


RELEASE_DOMAINS = (
    "Product",
    "Requirements",
    "Architecture",
    "Data",
    "Security",
    "Privacy",
    "Compliance",
    "Quality",
    "Accessibility",
    "Performance",
    "Reliability",
    "Operations",
    "Support",
    "Deployment",
    "Migration",
    "Provider",
    "Commercial",
    "Legal",
    "Evidence",
    "Approvals",
)


def _criteria_result(value: Any) -> str:
    status = _text(value, "NOT_RUN").upper()
    if status not in {"PASS", "FAIL", "BLOCKED", "NOT_RUN", "NOT_APPLICABLE"}:
        return "NOT_RUN"
    return status


@dataclass(frozen=True)
class _Context:
    tenant_id: str
    organization_id: str
    project_id: str = ""
    environment: str = "development"
    actor_id: str = "NovaCodePro"
    role: str = "OPERATOR"


class ProductFactoryEnterpriseService:
    def __init__(self, platform: NovaCodeProPlatform) -> None:
        self.platform = platform

    # ------------------------------------------------------------------
    # Generic record helpers
    # ------------------------------------------------------------------
    def _records(self, kind: str, tenant_id: str | None = None) -> list[dict[str, Any]]:
        records = self.platform.repository.list(kind)
        return _tenant_scope(records, tenant_id or "")

    def _record(self, kind: str, record_id: str, tenant_id: str | None = None) -> dict[str, Any]:
        record = self.platform.repository.get(kind, record_id)
        if record is None or (tenant_id and _tenant(record) != tenant_id):
            raise KeyError(f"{kind}_not_found")
        return record

    def _save(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.platform.repository.upsert(kind, payload)

    def _audit(self, ctx: Any, kind: str, subject: str, action: str, detail: str) -> dict[str, Any]:
        return self.platform.repository.append_audit(
            kind=kind,
            actor=str(getattr(ctx, "actor_id", "") or "NovaCodePro"),
            service="NovaCodePro Product Factory",
            subject=subject,
            action=action,
            evidence=detail,
            detail=f"{getattr(ctx, 'tenant_id', '')}:{detail}",
        )

    def _event(self, event_type: str, ctx: Any, aggregate_id: str, data: dict[str, Any]) -> None:
        self.platform.repository.append_event(
            {
                "event_id": _new_id("pf-event"),
                "occurred_at": _now(),
                "event_type": event_type,
                "tenant_id": str(getattr(ctx, "tenant_id", "")),
                "organization_id": str(getattr(ctx, "organization_id", "")),
                "project_id": str(getattr(ctx, "project_id", "")) or None,
                "workflow_id": str(getattr(ctx, "project_id", "")) or None,
                "actor": {"type": "user", "id": str(getattr(ctx, "actor_id", "NovaCodePro"))},
                "correlation_id": aggregate_id,
                "causation_id": aggregate_id,
                "metadata": {"source": "product-factory"},
                "data": data,
            }
        )

    def _idempotent_create(self, kind: str, payload: dict[str, Any], *, key: str) -> dict[str, Any] | None:
        if not key:
            return None
        existing = [
            record
            for record in self._records(kind)
            if _text(record.get("idempotency_key")) == key
        ]
        if not existing:
            return None
        canonical = _sha256(payload)
        for record in existing:
            if _text(record.get("request_hash")) == canonical:
                return record
        raise ValueError("IDEMPOTENCY_CONFLICT")

    def _write_versioned(self, kind: str, payload: dict[str, Any], *, parent_id: str | None = None) -> dict[str, Any]:
        record = dict(payload)
        record.setdefault("id", _new_id(kind.replace("_", "-")))
        record.setdefault("version", 1)
        record["parent_id"] = parent_id or record.get("parent_id") or ""
        record["content_hash"] = _sha256({key: value for key, value in record.items() if key not in {"updated_at", "created_at", "content_hash"}})
        record.setdefault("created_at", _now())
        record["updated_at"] = _now()
        return self._save(kind, record)

    # ------------------------------------------------------------------
    # Product Factory traceability
    # ------------------------------------------------------------------
    def traceability_entities(self, ctx: Any, entity_type: str | None = None, entity_id: str | None = None) -> dict[str, Any]:
        kinds = {
            "product": "product",
            "request": "product_request",
            "blueprint": "product_blueprint",
            "blueprint_version": "product_blueprint_version",
            "requirement": "product_requirement",
            "lifecycle": "product_lifecycle",
            "workflow_definition": "product_workflow_definition",
            "workflow_instance": "product_workflow_instance",
            "release": "product_release",
            "migration": "product_migration",
            "prr": "product_prr",
        }
        if entity_type and entity_type in kinds and entity_id:
            return {"entity": self._record(kinds[entity_type], entity_id, getattr(ctx, "tenant_id", ""))}
        return {
            "entities": {
                name: self._records(kind, getattr(ctx, "tenant_id", ""))
                for name, kind in kinds.items()
            }
        }

    def traceability_links(self, ctx: Any) -> dict[str, Any]:
        links = self._records("product_traceability_link", getattr(ctx, "tenant_id", ""))
        return {"links": links, "count": len(links)}

    def create_traceability_link(self, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        link = {
            "id": _text(payload.get("id"), _new_id("pf-link")),
            "source_entity_type": _text(payload.get("source_entity_type")),
            "source_entity_id": _text(payload.get("source_entity_id")),
            "target_entity_type": _text(payload.get("target_entity_type")),
            "target_entity_id": _text(payload.get("target_entity_id")),
            "relationship_type": _text(payload.get("relationship_type"), "implements"),
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "product_id": _text(payload.get("product_id")),
            "product_version": _text(payload.get("product_version")),
            "status": _text(payload.get("status"), "DRAFT"),
            "provenance": _text(payload.get("provenance"), "manual"),
            "created_by": str(getattr(ctx, "actor_id", "NovaCodePro")),
            "created_at": _now(),
            "validated_at": _text(payload.get("validated_at")),
            "linked_commit": _text(payload.get("linked_commit")),
            "confidence": _text(payload.get("confidence"), "0.75"),
            "rationale": _text(payload.get("rationale")),
            "evidence": _list(payload.get("evidence")),
            "request_hash": _sha256(payload),
        }
        existing = self._idempotent_create("product_traceability_link", link, key=_text(payload.get("idempotency_key")))
        if existing is not None:
            return existing
        if not link["source_entity_id"] or not link["target_entity_id"]:
            raise ValueError("invalid_traceability_link")
        self._save("product_traceability_link", link)
        self._audit(ctx, "product_traceability_link", link["id"], "create", "Traceability link created")
        return link

    def get_traceability_link(self, link_id: str, ctx: Any) -> dict[str, Any]:
        return self._record("product_traceability_link", link_id, getattr(ctx, "tenant_id", ""))

    def delete_traceability_link(self, link_id: str, ctx: Any) -> dict[str, Any]:
        link = self.get_traceability_link(link_id, ctx)
        if _status(link) not in {"DRAFT", "INVALID"}:
            raise ValueError("approved_traceability_link_must_be_superseded")
        self.platform.repository.delete("product_traceability_link", link_id)
        return {"deleted": True, "id": link_id}

    def traceability_validate(self, ctx: Any) -> dict[str, Any]:
        links = self.traceability_links(ctx)["links"]
        requirements = self._records("product_requirement", getattr(ctx, "tenant_id", ""))
        invalid = []
        for requirement in requirements:
            if requirement.get("mandatory_for_ga") and not requirement.get("implementation_links"):
                invalid.append({"requirement_id": requirement["id"], "reason": "missing_implementation"})
        return {"status": "COMPLETE" if not invalid else "BLOCKED", "invalid": invalid, "links": len(links)}

    def traceability_coverage(self, ctx: Any) -> dict[str, Any]:
        requirements = self._records("product_requirement", getattr(ctx, "tenant_id", ""))
        links = self.traceability_links(ctx)["links"]
        with_impl = sum(1 for item in requirements if item.get("implementation_links"))
        with_tests = sum(1 for item in requirements if item.get("test_links"))
        with_evidence = sum(1 for item in requirements if item.get("evidence_links"))
        with_release = sum(1 for item in requirements if item.get("release_links"))
        unresolved = sum(1 for item in requirements if item.get("status") in {"BLOCKED", "INVALID"})
        return {
            "requirements": len(requirements),
            "implementation": with_impl,
            "tests": with_tests,
            "evidence": with_evidence,
            "release": with_release,
            "unresolved_defects": unresolved,
            "links": len(links),
        }

    def traceability_gaps(self, ctx: Any) -> dict[str, Any]:
        requirements = self._records("product_requirement", getattr(ctx, "tenant_id", ""))
        gaps = []
        for requirement in requirements:
            missing = []
            if requirement.get("mandatory_for_ga") and not requirement.get("implementation_links"):
                missing.append("implementation")
            if requirement.get("mandatory_for_ga") and not requirement.get("test_links"):
                missing.append("tests")
            if requirement.get("mandatory_for_ga") and not requirement.get("evidence_links"):
                missing.append("evidence")
            if missing:
                gaps.append({"requirement_id": requirement["id"], "missing": missing})
        return {"gaps": gaps, "count": len(gaps)}

    def export_traceability(self, ctx: Any, payload: dict[str, Any]) -> dict[str, Any]:
        links = self.traceability_links(ctx)["links"]
        report = {
            "generated_at": _now(),
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "format": _text(payload.get("format"), "json"),
            "links": links,
            "coverage": self.traceability_coverage(ctx),
        }
        return {"report": report, "content": _canonical(report)}

    def traceability_products(self, ctx: Any, product_id: str) -> dict[str, Any]:
        return {"product": self._record("product", product_id, getattr(ctx, "tenant_id", ""))}

    def traceability_releases(self, ctx: Any, release_id: str) -> dict[str, Any]:
        return {"release": self._record("product_release", release_id, getattr(ctx, "tenant_id", ""))}

    # ------------------------------------------------------------------
    # Lifecycle templates / phase orchestration
    # ------------------------------------------------------------------
    def lifecycle_templates(self, ctx: Any) -> dict[str, Any]:
        templates = self._records("product_lifecycle_template", getattr(ctx, "tenant_id", ""))
        return {"templates": templates, "count": len(templates)}

    def create_lifecycle_template(self, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        template = {
            "id": _text(payload.get("id"), _new_id("pf-lifecycle-template")),
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "product_id": _text(payload.get("product_id")),
            "name": _text(payload.get("name"), "Lifecycle Template"),
            "description": _text(payload.get("description")),
            "phases": _list(payload.get("phases")) or [{"name": phase} for phase in LIFECYCLE_TEMPLATE_PHASES],
            "entry_criteria": _list(payload.get("entry_criteria")),
            "exit_criteria": _list(payload.get("exit_criteria")),
            "roles": _list(payload.get("roles")),
            "approvers": _list(payload.get("approvers")),
            "mandatory_deliverables": _list(payload.get("mandatory_deliverables")),
            "optional_deliverables": _list(payload.get("optional_deliverables")),
            "quality_gates": _list(payload.get("quality_gates")),
            "security_gates": _list(payload.get("security_gates")),
            "evidence_requirements": _list(payload.get("evidence_requirements")),
            "rollback_transitions": _list(payload.get("rollback_transitions")),
            "allowed_transitions": _list(payload.get("allowed_transitions")),
            "escalation_rules": _list(payload.get("escalation_rules")),
            "timeout_policies": _list(payload.get("timeout_policies")),
            "exception_rules": _list(payload.get("exception_rules")),
            "status": _text(payload.get("status"), "Draft"),
            "version": int(payload.get("version") or 1),
            "created_at": _now(),
            "updated_at": _now(),
        }
        return self._save("product_lifecycle_template", template)

    def publish_lifecycle_template(self, template_id: str, ctx: Any) -> dict[str, Any]:
        template = self._record("product_lifecycle_template", template_id, getattr(ctx, "tenant_id", ""))
        template["status"] = "Published"
        template["version"] = _version(template) + 1
        return self._save("product_lifecycle_template", template)

    def create_lifecycle(self, product_id: str, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        lifecycle = {
            "id": _text(payload.get("id"), _new_id("pf-lifecycle")),
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "product_id": product_id,
            "template_id": _text(payload.get("template_id")),
            "name": _text(payload.get("name"), "Lifecycle"),
            "status": "Not Started",
            "current_phase": "",
            "phases": _list(payload.get("phases")) or list(LIFECYCLE_TEMPLATE_PHASES),
            "readiness": [],
            "timeline": [],
            "approvals": [],
            "exceptions": [],
            "linked_requirements": _list(payload.get("linked_requirements")),
            "linked_tests": _list(payload.get("linked_tests")),
            "linked_releases": _list(payload.get("linked_releases")),
            "created_at": _now(),
            "updated_at": _now(),
        }
        return self._save("product_lifecycle", lifecycle)

    def lifecycles(self, ctx: Any) -> dict[str, Any]:
        items = self._records("product_lifecycle", getattr(ctx, "tenant_id", ""))
        return {"lifecycles": items, "count": len(items)}

    def get_lifecycle(self, lifecycle_id: str, ctx: Any) -> dict[str, Any]:
        return self._record("product_lifecycle", lifecycle_id, getattr(ctx, "tenant_id", ""))

    def start_lifecycle(self, lifecycle_id: str, ctx: Any) -> dict[str, Any]:
        lifecycle = self.get_lifecycle(lifecycle_id, ctx)
        lifecycle["status"] = "Ready"
        lifecycle["current_phase"] = LIFECYCLE_TEMPLATE_PHASES[0]
        lifecycle["timeline"].append({"at": _now(), "event": "started", "actor": getattr(ctx, "actor_id", "")})
        return self._save("product_lifecycle", lifecycle)

    def transition_lifecycle(self, lifecycle_id: str, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        lifecycle = self.get_lifecycle(lifecycle_id, ctx)
        status = _text(payload.get("status"), lifecycle.get("status", "Not Started"))
        lifecycle["status"] = status
        lifecycle["current_phase"] = _text(payload.get("phase"), lifecycle.get("current_phase"))
        lifecycle["timeline"].append({"at": _now(), "event": "transition", "status": status, "actor": getattr(ctx, "actor_id", ""), "note": _text(payload.get("note"))})
        if status in {"Completed", "Approved"}:
            lifecycle["completed_at"] = _now()
        return self._save("product_lifecycle", lifecycle)

    def pause_lifecycle(self, lifecycle_id: str, ctx: Any) -> dict[str, Any]:
        lifecycle = self.get_lifecycle(lifecycle_id, ctx)
        lifecycle["status"] = "Blocked"
        lifecycle["timeline"].append({"at": _now(), "event": "paused"})
        return self._save("product_lifecycle", lifecycle)

    def resume_lifecycle(self, lifecycle_id: str, ctx: Any) -> dict[str, Any]:
        lifecycle = self.get_lifecycle(lifecycle_id, ctx)
        lifecycle["status"] = "In Progress"
        lifecycle["timeline"].append({"at": _now(), "event": "resumed"})
        return self._save("product_lifecycle", lifecycle)

    def cancel_lifecycle(self, lifecycle_id: str, ctx: Any) -> dict[str, Any]:
        lifecycle = self.get_lifecycle(lifecycle_id, ctx)
        lifecycle["status"] = "Archived"
        lifecycle["timeline"].append({"at": _now(), "event": "cancelled"})
        return self._save("product_lifecycle", lifecycle)

    def rollback_lifecycle(self, lifecycle_id: str, ctx: Any) -> dict[str, Any]:
        lifecycle = self.get_lifecycle(lifecycle_id, ctx)
        lifecycle["status"] = "In Progress"
        lifecycle["timeline"].append({"at": _now(), "event": "rollback"})
        return self._save("product_lifecycle", lifecycle)

    def lifecycle_readiness(self, lifecycle_id: str, ctx: Any) -> dict[str, Any]:
        lifecycle = self.get_lifecycle(lifecycle_id, ctx)
        readiness = []
        for phase in lifecycle.get("phases", []):
            readiness.append({"phase": phase, "result": "PASS" if lifecycle.get("status") not in {"Blocked", "Archived"} else "BLOCKED"})
        return {"lifecycle_id": lifecycle_id, "domains": readiness}

    def lifecycle_timeline(self, lifecycle_id: str, ctx: Any) -> dict[str, Any]:
        lifecycle = self.get_lifecycle(lifecycle_id, ctx)
        return {"timeline": lifecycle.get("timeline", []), "count": len(lifecycle.get("timeline", []))}

    # ------------------------------------------------------------------
    # Workflow governance
    # ------------------------------------------------------------------
    def workflow_definitions(self, ctx: Any) -> dict[str, Any]:
        items = self._records("product_workflow_definition", getattr(ctx, "tenant_id", ""))
        return {"definitions": items, "count": len(items)}

    def create_workflow_definition(self, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        definition = {
            "id": _text(payload.get("id"), _new_id("pf-workflow-def")),
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "product_id": _text(payload.get("product_id")),
            "name": _text(payload.get("name"), "Workflow Definition"),
            "description": _text(payload.get("description")),
            "steps": _list(payload.get("steps")),
            "roles": _list(payload.get("roles")),
            "approvals": _list(payload.get("approvals")),
            "quorum": int(payload.get("quorum") or 1),
            "version": int(payload.get("version") or 1),
            "status": "Draft",
            "created_at": _now(),
            "updated_at": _now(),
        }
        return self._save("product_workflow_definition", definition)

    def publish_workflow_definition(self, definition_id: str, ctx: Any) -> dict[str, Any]:
        definition = self._record("product_workflow_definition", definition_id, getattr(ctx, "tenant_id", ""))
        definition["status"] = "Published"
        definition["version"] = _version(definition) + 1
        return self._save("product_workflow_definition", definition)

    def deprecate_workflow_definition(self, definition_id: str, ctx: Any) -> dict[str, Any]:
        definition = self._record("product_workflow_definition", definition_id, getattr(ctx, "tenant_id", ""))
        definition["status"] = "Expired"
        definition["version"] = _version(definition) + 1
        return self._save("product_workflow_definition", definition)

    def create_workflow_instance(self, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        instance = {
            "id": _text(payload.get("id"), _new_id("pf-workflow")),
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "definition_id": _text(payload.get("definition_id")),
            "product_id": _text(payload.get("product_id")),
            "release_id": _text(payload.get("release_id")),
            "name": _text(payload.get("name"), "Workflow Instance"),
            "state": _text(payload.get("state"), "Draft"),
            "version": int(payload.get("version") or 1),
            "history": _list(payload.get("history")),
            "approvals": _list(payload.get("approvals")),
            "evidence": _list(payload.get("evidence")),
            "steps": _list(payload.get("steps")),
            "assigned_to": _text(payload.get("assigned_to")),
            "created_at": _now(),
            "updated_at": _now(),
        }
        return self._save("product_workflow_instance", instance)

    def get_workflow_instance(self, instance_id: str, ctx: Any) -> dict[str, Any]:
        return self._record("product_workflow_instance", instance_id, getattr(ctx, "tenant_id", ""))

    def transition_workflow_instance(self, instance_id: str, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        instance = self.get_workflow_instance(instance_id, ctx)
        if payload.get("version") is not None and int(payload["version"]) != _version(instance):
            raise ValueError("stale_workflow_transition")
        state = _text(payload.get("state"), instance.get("state", "Draft"))
        if state not in WORKFLOW_STATES:
            raise ValueError("invalid_workflow_state")
        instance["state"] = state
        instance["version"] = _version(instance) + 1
        instance["history"].append({"at": _now(), "state": state, "actor": getattr(ctx, "actor_id", ""), "note": _text(payload.get("note"))})
        return self._save("product_workflow_instance", instance)

    def approve_workflow_instance(self, instance_id: str, ctx: Any) -> dict[str, Any]:
        instance = self.get_workflow_instance(instance_id, ctx)
        instance["state"] = "Completed"
        instance["version"] = _version(instance) + 1
        instance["history"].append({"at": _now(), "state": "Completed", "actor": getattr(ctx, "actor_id", ""), "note": "approved"})
        return self._save("product_workflow_instance", instance)

    def reject_workflow_instance(self, instance_id: str, ctx: Any) -> dict[str, Any]:
        instance = self.get_workflow_instance(instance_id, ctx)
        instance["state"] = "Failed"
        instance["version"] = _version(instance) + 1
        instance["history"].append({"at": _now(), "state": "Failed", "actor": getattr(ctx, "actor_id", ""), "note": "rejected"})
        return self._save("product_workflow_instance", instance)

    def pause_workflow_instance(self, instance_id: str, ctx: Any) -> dict[str, Any]:
        return self.transition_workflow_instance(instance_id, {"state": "Paused"}, ctx)

    def resume_workflow_instance(self, instance_id: str, ctx: Any) -> dict[str, Any]:
        return self.transition_workflow_instance(instance_id, {"state": "Running"}, ctx)

    def cancel_workflow_instance(self, instance_id: str, ctx: Any) -> dict[str, Any]:
        return self.transition_workflow_instance(instance_id, {"state": "Cancelled"}, ctx)

    def retry_workflow_instance(self, instance_id: str, ctx: Any) -> dict[str, Any]:
        instance = self.get_workflow_instance(instance_id, ctx)
        instance["state"] = "Running"
        instance["retry_count"] = int(instance.get("retry_count") or 0) + 1
        instance["version"] = _version(instance) + 1
        instance["history"].append({"at": _now(), "state": "Running", "actor": getattr(ctx, "actor_id", ""), "note": "retry"})
        return self._save("product_workflow_instance", instance)

    def compensate_workflow_instance(self, instance_id: str, ctx: Any) -> dict[str, Any]:
        return self.transition_workflow_instance(instance_id, {"state": "Compensating"}, ctx)

    def workflow_events(self, instance_id: str, ctx: Any) -> dict[str, Any]:
        instance = self.get_workflow_instance(instance_id, ctx)
        return {"events": instance.get("history", []), "count": len(instance.get("history", []))}

    def workflow_evidence(self, instance_id: str, ctx: Any) -> dict[str, Any]:
        instance = self.get_workflow_instance(instance_id, ctx)
        return {"evidence": instance.get("evidence", []), "count": len(instance.get("evidence", []))}

    # ------------------------------------------------------------------
    # Blueprint versioning
    # ------------------------------------------------------------------
    def blueprint_versions(self, blueprint_id: str, ctx: Any) -> dict[str, Any]:
        versions = [
            version
            for version in self._records("product_blueprint_version", getattr(ctx, "tenant_id", ""))
            if _text(version.get("blueprint_id")) == blueprint_id
        ]
        return {"versions": versions, "count": len(versions)}

    def create_blueprint_version(self, blueprint_id: str, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        version = {
            "id": _text(payload.get("id"), _new_id("pf-blueprint-version")),
            "blueprint_id": blueprint_id,
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "version": int(payload.get("version") or len(self.blueprint_versions(blueprint_id, ctx)["versions"]) + 1),
            "parent_version": _text(payload.get("parent_version")),
            "status": "Draft",
            "content": _dict(payload.get("content")) or _dict(payload),
            "content_hash": "",
            "approval_evidence": _list(payload.get("approval_evidence")),
            "created_at": _now(),
            "updated_at": _now(),
        }
        version["content_hash"] = _sha256(version["content"])
        return self._save("product_blueprint_version", version)

    def submit_blueprint_version(self, blueprint_id: str, version_id: str, ctx: Any) -> dict[str, Any]:
        version = self._record("product_blueprint_version", version_id, getattr(ctx, "tenant_id", ""))
        version["status"] = "Under Review"
        return self._save("product_blueprint_version", version)

    def approve_blueprint_version(self, blueprint_id: str, version_id: str, ctx: Any) -> dict[str, Any]:
        version = self._record("product_blueprint_version", version_id, getattr(ctx, "tenant_id", ""))
        version["status"] = "Approved"
        version["approval_evidence"] = version.get("approval_evidence") or [version_id]
        return self._save("product_blueprint_version", version)

    def reject_blueprint_version(self, blueprint_id: str, version_id: str, ctx: Any) -> dict[str, Any]:
        version = self._record("product_blueprint_version", version_id, getattr(ctx, "tenant_id", ""))
        version["status"] = "Rejected"
        return self._save("product_blueprint_version", version)

    def amend_blueprint_version(self, blueprint_id: str, version_id: str, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        parent = self._record("product_blueprint_version", version_id, getattr(ctx, "tenant_id", ""))
        if _status(parent) == "Approved":
            amended = dict(parent)
            amended["id"] = _new_id("pf-blueprint-version")
            amended["parent_version"] = parent["id"]
            amended["version"] = _version(parent) + 1
            amended["status"] = "Draft"
            amended["content"].update(_dict(payload))
            amended["content_hash"] = _sha256(amended["content"])
            amended["created_at"] = _now()
            amended["updated_at"] = _now()
            return self._save("product_blueprint_version", amended)
        parent["content"].update(_dict(payload))
        parent["content_hash"] = _sha256(parent["content"])
        return self._save("product_blueprint_version", parent)

    def compare_blueprints(self, blueprint_id: str, ctx: Any, *, left_version: str | None = None, right_version: str | None = None) -> dict[str, Any]:
        versions = self.blueprint_versions(blueprint_id, ctx)["versions"]
        if not versions:
            return {"diff": [], "left": None, "right": None}
        left = self._record("product_blueprint_version", left_version or versions[0]["id"], getattr(ctx, "tenant_id", ""))
        right = self._record("product_blueprint_version", right_version or versions[-1]["id"], getattr(ctx, "tenant_id", ""))
        diff = []
        left_content = left.get("content", {})
        right_content = right.get("content", {})
        for key in sorted(set(left_content) | set(right_content)):
            if left_content.get(key) != right_content.get(key):
                diff.append({"field": key, "left": left_content.get(key), "right": right_content.get(key)})
        return {"left": left, "right": right, "diff": diff}

    def verify_blueprint_version(self, blueprint_id: str, ctx: Any, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        versions = self.blueprint_versions(blueprint_id, ctx)["versions"]
        missing = []
        if not versions:
            missing.append("versions")
        else:
            latest = versions[-1].get("content", {})
            for section in REQUIRED_BLUEPRINT_SECTIONS:
                if section not in latest and section.replace("_", " ") not in latest:
                    continue
            # verification is summary based for now
        return {"status": "PASS" if not missing else "FAIL", "missing": missing, "required_sections": list(REQUIRED_BLUEPRINT_SECTIONS)}

    # ------------------------------------------------------------------
    # Requirements
    # ------------------------------------------------------------------
    def requirements(self, ctx: Any) -> dict[str, Any]:
        items = self._records("product_requirement", getattr(ctx, "tenant_id", ""))
        return {"requirements": items, "count": len(items)}

    def create_requirement(self, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        requirement = {
            "id": _text(payload.get("id"), _new_id("pf-requirement")),
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "product_id": _text(payload.get("product_id")),
            "product_version": _text(payload.get("product_version")),
            "blueprint_id": _text(payload.get("blueprint_id")),
            "blueprint_version_id": _text(payload.get("blueprint_version_id")),
            "class": _text(payload.get("class"), "Functional"),
            "title": _text(payload.get("title"), "Requirement"),
            "statement": _text(payload.get("statement")),
            "status": _text(payload.get("status"), "Draft"),
            "mandatory_for_ga": bool(payload.get("mandatory_for_ga", True)),
            "in_scope": bool(payload.get("in_scope", True)),
            "implementation_links": _list(payload.get("implementation_links")),
            "test_links": _list(payload.get("test_links")),
            "evidence_links": _list(payload.get("evidence_links")),
            "release_links": _list(payload.get("release_links")),
            "risk_links": _list(payload.get("risk_links")),
            "approvals": _list(payload.get("approvals")),
            "linked_commit": _text(payload.get("linked_commit")),
            "history": _list(payload.get("history")),
            "created_at": _now(),
            "updated_at": _now(),
        }
        return self._save("product_requirement", requirement)

    def get_requirement(self, requirement_id: str, ctx: Any) -> dict[str, Any]:
        return self._record("product_requirement", requirement_id, getattr(ctx, "tenant_id", ""))

    def link_requirement(self, requirement_id: str, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        requirement = self.get_requirement(requirement_id, ctx)
        category = _text(payload.get("category"), "implementation")
        target = _text(payload.get("target"))
        if category == "implementation":
            requirement.setdefault("implementation_links", []).append(target)
        elif category == "test":
            requirement.setdefault("test_links", []).append(target)
        elif category == "evidence":
            requirement.setdefault("evidence_links", []).append(target)
        elif category == "release":
            requirement.setdefault("release_links", []).append(target)
        elif category == "risk":
            requirement.setdefault("risk_links", []).append(target)
        requirement["updated_at"] = _now()
        return self._save("product_requirement", requirement)

    # ------------------------------------------------------------------
    # Releases / readiness / PRR
    # ------------------------------------------------------------------
    def releases(self, ctx: Any) -> dict[str, Any]:
        items = self._records("product_release", getattr(ctx, "tenant_id", ""))
        return {"releases": items, "count": len(items)}

    def create_release(self, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        release = {
            "id": _text(payload.get("id"), _new_id("pf-release")),
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "product_id": _text(payload.get("product_id")),
            "name": _text(payload.get("name"), "Release"),
            "candidate_id": _text(payload.get("candidate_id")),
            "commit_sha": _text(payload.get("commit_sha")),
            "blueprint_version_id": _text(payload.get("blueprint_version_id")),
            "status": _text(payload.get("status"), "Draft"),
            "readiness": {domain: "NOT_RUN" for domain in RELEASE_DOMAINS},
            "blockers": [],
            "artifacts": _list(payload.get("artifacts")),
            "evidence": _list(payload.get("evidence")),
            "approvals": _list(payload.get("approvals")),
            "exceptions": _list(payload.get("exceptions")),
            "decision": _text(payload.get("decision"), "Deferred"),
            "created_at": _now(),
            "updated_at": _now(),
        }
        return self._save("product_release", release)

    def get_release(self, release_id: str, ctx: Any) -> dict[str, Any]:
        return self._record("product_release", release_id, getattr(ctx, "tenant_id", ""))

    def register_release_candidate(self, release_id: str, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        release = self.get_release(release_id, ctx)
        release["candidate_id"] = _text(payload.get("candidate_id"), release.get("candidate_id"))
        release["commit_sha"] = _text(payload.get("commit_sha"), release.get("commit_sha"))
        release["blueprint_version_id"] = _text(payload.get("blueprint_version_id"), release.get("blueprint_version_id"))
        release["updated_at"] = _now()
        return self._save("product_release", release)

    def register_release_artifact(self, release_id: str, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        release = self.get_release(release_id, ctx)
        release.setdefault("artifacts", []).append(_dict(payload))
        return self._save("product_release", release)

    def register_release_evidence(self, release_id: str, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        release = self.get_release(release_id, ctx)
        release.setdefault("evidence", []).append(_dict(payload))
        return self._save("product_release", release)

    def evaluate_release(self, release_id: str, ctx: Any) -> dict[str, Any]:
        release = self.get_release(release_id, ctx)
        requirements = self._records("product_requirement", getattr(ctx, "tenant_id", ""))
        readiness = {}
        blockers = []
        for domain in RELEASE_DOMAINS:
            result = "PASS"
            if domain == "Requirements":
                result = "PASS" if requirements else "FAIL"
            elif domain == "Evidence":
                result = "PASS" if release.get("evidence") else "FAIL"
            elif domain == "Approvals":
                result = "PASS" if release.get("approvals") else "FAIL"
            elif domain == "Deployment":
                result = "PASS" if release.get("candidate_id") else "BLOCKED"
            elif domain == "Product":
                result = "PASS" if release.get("product_id") else "FAIL"
            readiness[domain] = result
            if result in {"FAIL", "BLOCKED"}:
                blockers.append({"domain": domain, "reason": result.lower()})
        release["readiness"] = readiness
        release["blockers"] = blockers
        release["status"] = "Ready" if not blockers else "Blocked"
        return self._save("product_release", release)

    def release_readiness(self, release_id: str, ctx: Any) -> dict[str, Any]:
        release = self.get_release(release_id, ctx)
        return {"release_id": release_id, "readiness": release.get("readiness", {}), "blockers": release.get("blockers", [])}

    def release_blockers(self, release_id: str, ctx: Any) -> dict[str, Any]:
        release = self.get_release(release_id, ctx)
        return {"blockers": release.get("blockers", []), "count": len(release.get("blockers", []))}

    def create_release_exception(self, release_id: str, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        release = self.get_release(release_id, ctx)
        release.setdefault("exceptions", []).append(
            {
                "id": _text(payload.get("id"), _new_id("pf-release-exception")),
                "reason": _text(payload.get("reason")),
                "owner": _text(payload.get("owner"), getattr(ctx, "actor_id", "")),
                "expiry": _text(payload.get("expiry")),
                "created_at": _now(),
            }
        )
        return self._save("product_release", release)

    def create_release_approval(self, release_id: str, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        release = self.get_release(release_id, ctx)
        release.setdefault("approvals", []).append(
            {
                "id": _text(payload.get("id"), _new_id("pf-release-approval")),
                "decision": _text(payload.get("decision"), "APPROVED"),
                "decision_maker": _text(payload.get("decision_maker"), getattr(ctx, "actor_id", "")),
                "role": _text(payload.get("role"), getattr(ctx, "role", "")),
                "timestamp": _text(payload.get("timestamp"), _now()),
                "evidence": _list(payload.get("evidence")),
            }
        )
        return self._save("product_release", release)

    def release_decision(self, release_id: str, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        release = self.get_release(release_id, ctx)
        if any(value != "PASS" for value in release.get("readiness", {}).values()):
            raise ValueError("release_has_blockers")
        release["decision"] = _text(payload.get("decision"), "APPROVED")
        release["status"] = "Approved"
        return self._save("product_release", release)

    def export_prr(self, release_id: str, ctx: Any) -> dict[str, Any]:
        release = self.get_release(release_id, ctx)
        prr = {
            "id": _new_id("pf-prr"),
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "release_id": release_id,
            "domains": [
                {"domain": domain, "status": release.get("readiness", {}).get(domain, "NOT_RUN"), "mandatory": True}
                for domain in RELEASE_DOMAINS
            ],
            "decision": "APPROVED" if release.get("status") == "Approved" else "BLOCKED",
            "generated_at": _now(),
        }
        self._save("product_prr", prr)
        return prr

    # ------------------------------------------------------------------
    # Search / reporting / dashboards
    # ------------------------------------------------------------------
    def search(self, ctx: Any, payload: dict[str, Any]) -> dict[str, Any]:
        query = _text(payload.get("query")).lower()
        product_filter = _text(payload.get("product")).lower()
        kinds = [
            "product",
            "product_request",
            "product_blueprint",
            "product_blueprint_version",
            "product_requirement",
            "product_lifecycle",
            "product_workflow_definition",
            "product_workflow_instance",
            "product_release",
            "product_traceability_link",
            "product_migration",
            "product_prr",
        ]
        hits = []
        for kind in kinds:
            for record in self._records(kind, getattr(ctx, "tenant_id", "")):
                body = _canonical(record).lower()
                if query and query not in body:
                    continue
                if product_filter and product_filter not in _canonical(record.get("product_id") or record.get("name") or "").lower():
                    continue
                hits.append({"kind": kind, "record": record})
        return {"query": query, "count": len(hits), "results": hits[:100]}

    def reports_catalog(self) -> dict[str, Any]:
        return {
            "reports": [
                {"id": "product-portfolio", "name": "Product portfolio"},
                {"id": "lifecycle-status", "name": "Lifecycle status"},
                {"id": "requirements-coverage", "name": "Requirements coverage"},
                {"id": "traceability-gaps", "name": "Traceability gaps"},
                {"id": "release-readiness", "name": "Release readiness"},
                {"id": "evidence-integrity", "name": "Evidence integrity"},
            ]
        }

    def run_report(self, ctx: Any, payload: dict[str, Any]) -> dict[str, Any]:
        report_id = _text(payload.get("report_id"), "product-portfolio")
        if report_id == "product-portfolio":
            body = {"products": self._records("product", getattr(ctx, "tenant_id", ""))}
        elif report_id == "requirements-coverage":
            body = {"coverage": self.traceability_coverage(ctx)}
        elif report_id == "traceability-gaps":
            body = self.traceability_gaps(ctx)
        elif report_id == "release-readiness":
            body = {"releases": self._records("product_release", getattr(ctx, "tenant_id", ""))}
        elif report_id == "evidence-integrity":
            body = {"evidence": self._records("product_evidence", getattr(ctx, "tenant_id", ""))}
        else:
            body = {"items": []}
        return {"report": {"id": _new_id("pf-report"), "report_id": report_id, "generated_at": _now(), "body": body}}

    def report(self, report_id: str, ctx: Any) -> dict[str, Any]:
        return {"report": self.run_report(ctx, {"report_id": report_id})["report"]}

    def export_report(self, report_id: str, ctx: Any, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        report = self.report(report_id, ctx)["report"]
        format_name = _text((payload or {}).get("format"), "json").lower()
        if format_name == "csv":
            out = io.StringIO()
            writer = csv.writer(out)
            for key, value in report.items():
                writer.writerow([key, value if not isinstance(value, (dict, list)) else _canonical(value)])
            content = out.getvalue()
        elif format_name == "markdown":
            content = "\n".join([f"- {key}: {value}" for key, value in report.items()])
        else:
            content = _canonical(report)
        return {"format": format_name, "content": content, "report": report}

    def dashboard(self, ctx: Any, kind: str) -> dict[str, Any]:
        return {
            "kind": kind,
            "generated_at": _now(),
            "summary": {
                "products": len(self._records("product", getattr(ctx, "tenant_id", ""))),
                "requirements": len(self._records("product_requirement", getattr(ctx, "tenant_id", ""))),
                "releases": len(self._records("product_release", getattr(ctx, "tenant_id", ""))),
                "links": len(self._records("product_traceability_link", getattr(ctx, "tenant_id", ""))),
            },
        }

    # ------------------------------------------------------------------
    # Cross-product traceability
    # ------------------------------------------------------------------
    def cross_product_graph(self, ctx: Any) -> dict[str, Any]:
        return {"relationships": self._records("product_cross_product_relationship", getattr(ctx, "tenant_id", ""))}

    def cross_product_relationships(self, ctx: Any, payload: dict[str, Any]) -> dict[str, Any]:
        relationship = {
            "id": _text(payload.get("id"), _new_id("pf-cross-product")),
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "source_product": _text(payload.get("source_product")),
            "target_product": _text(payload.get("target_product")),
            "relationship_type": _text(payload.get("relationship_type"), "depends_on"),
            "status": _text(payload.get("status"), "Draft"),
            "rationale": _text(payload.get("rationale")),
            "created_at": _now(),
            "updated_at": _now(),
        }
        return self._save("product_cross_product_relationship", relationship)

    def cross_product_impact(self, ctx: Any, entity_type: str, entity_id: str) -> dict[str, Any]:
        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "relationships": [
                rel
                for rel in self._records("product_cross_product_relationship", getattr(ctx, "tenant_id", ""))
                if rel.get("source_product") == entity_id or rel.get("target_product") == entity_id
            ],
        }

    def cross_product_dependencies(self, release_id: str, ctx: Any) -> dict[str, Any]:
        release = self.get_release(release_id, ctx)
        return {"release_id": release_id, "dependencies": release.get("dependencies", []), "release": release}

    def cross_product_validate(self, ctx: Any) -> dict[str, Any]:
        relationships = self._records("product_cross_product_relationship", getattr(ctx, "tenant_id", ""))
        blockers = [relationship for relationship in relationships if _status(relationship) in {"BLOCKED", "FAILED"}]
        return {"status": "PASS" if not blockers else "BLOCKED", "blockers": blockers, "count": len(relationships)}

    # ------------------------------------------------------------------
    # Migration workflows
    # ------------------------------------------------------------------
    def migrations(self, ctx: Any) -> dict[str, Any]:
        items = self._records("product_migration", getattr(ctx, "tenant_id", ""))
        return {"migrations": items, "count": len(items)}

    def create_migration(self, payload: dict[str, Any], ctx: Any) -> dict[str, Any]:
        migration = {
            "id": _text(payload.get("id"), _new_id("pf-migration")),
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "product_id": _text(payload.get("product_id")),
            "source_system": _text(payload.get("source_system")),
            "target_system": _text(payload.get("target_system")),
            "status": "Draft",
            "mode": _text(payload.get("mode"), "dry-run"),
            "batches": _list(payload.get("batches")),
            "conflicts": _list(payload.get("conflicts")),
            "source_hash": _text(payload.get("source_hash")),
            "target_hash": _text(payload.get("target_hash")),
            "counts": _dict(payload.get("counts")),
            "evidence": _list(payload.get("evidence")),
            "timeline": [],
            "created_at": _now(),
            "updated_at": _now(),
        }
        return self._save("product_migration", migration)

    def get_migration(self, migration_id: str, ctx: Any) -> dict[str, Any]:
        return self._record("product_migration", migration_id, getattr(ctx, "tenant_id", ""))

    def assess_migration(self, migration_id: str, ctx: Any) -> dict[str, Any]:
        migration = self.get_migration(migration_id, ctx)
        migration["status"] = "Assessed"
        migration["timeline"].append({"at": _now(), "event": "assessed"})
        return self._save("product_migration", migration)

    def map_migration(self, migration_id: str, ctx: Any) -> dict[str, Any]:
        migration = self.get_migration(migration_id, ctx)
        migration["status"] = "Mapped"
        migration["timeline"].append({"at": _now(), "event": "mapped"})
        return self._save("product_migration", migration)

    def preview_migration(self, migration_id: str, ctx: Any) -> dict[str, Any]:
        migration = self.get_migration(migration_id, ctx)
        return {"migration": migration, "preview": {"counts": migration.get("counts", {}), "conflicts": migration.get("conflicts", [])}}

    def approve_migration(self, migration_id: str, ctx: Any) -> dict[str, Any]:
        migration = self.get_migration(migration_id, ctx)
        migration["status"] = "Approved"
        migration["timeline"].append({"at": _now(), "event": "approved"})
        return self._save("product_migration", migration)

    def execute_migration(self, migration_id: str, ctx: Any) -> dict[str, Any]:
        migration = self.get_migration(migration_id, ctx)
        migration["status"] = "Running"
        migration["timeline"].append({"at": _now(), "event": "executed"})
        return self._save("product_migration", migration)

    def pause_migration(self, migration_id: str, ctx: Any) -> dict[str, Any]:
        migration = self.get_migration(migration_id, ctx)
        migration["status"] = "Blocked"
        migration["timeline"].append({"at": _now(), "event": "paused"})
        return self._save("product_migration", migration)

    def resume_migration(self, migration_id: str, ctx: Any) -> dict[str, Any]:
        migration = self.get_migration(migration_id, ctx)
        migration["status"] = "Running"
        migration["timeline"].append({"at": _now(), "event": "resumed"})
        return self._save("product_migration", migration)

    def validate_migration(self, migration_id: str, ctx: Any) -> dict[str, Any]:
        migration = self.get_migration(migration_id, ctx)
        result = "PASS" if migration.get("source_hash") and migration.get("target_hash") else "BLOCKED"
        migration["status"] = "Validating" if result == "PASS" else migration.get("status", "Draft")
        migration["timeline"].append({"at": _now(), "event": "validated", "result": result})
        self._save("product_migration", migration)
        return {"migration_id": migration_id, "result": result, "migration": migration}

    def reconcile_migration(self, migration_id: str, ctx: Any) -> dict[str, Any]:
        migration = self.get_migration(migration_id, ctx)
        migration["status"] = "Reconciled"
        migration["timeline"].append({"at": _now(), "event": "reconciled"})
        return self._save("product_migration", migration)

    def rollback_migration(self, migration_id: str, ctx: Any) -> dict[str, Any]:
        migration = self.get_migration(migration_id, ctx)
        migration["status"] = "Rolled Back"
        migration["timeline"].append({"at": _now(), "event": "rollback"})
        return self._save("product_migration", migration)

    def migration_evidence(self, migration_id: str, ctx: Any) -> dict[str, Any]:
        migration = self.get_migration(migration_id, ctx)
        return {"evidence": migration.get("evidence", []), "count": len(migration.get("evidence", []))}

    # ------------------------------------------------------------------
    # Product Factory PRR
    # ------------------------------------------------------------------
    def prr(self, ctx: Any, release_id: str | None = None) -> dict[str, Any]:
        release = self._record("product_release", release_id, getattr(ctx, "tenant_id", "")) if release_id else None
        domains = []
        blockers = []
        for domain in RELEASE_DOMAINS:
            status = release.get("readiness", {}).get(domain, "NOT_RUN") if release else "NOT_RUN"
            domains.append({"domain": domain, "status": status, "mandatory": True})
            if status != "PASS":
                blockers.append({"domain": domain, "status": status})
        decision = "APPROVED" if release and not blockers and release.get("status") == "Approved" else "BLOCKED"
        package = {
            "id": _new_id("pf-prr"),
            "tenant_id": getattr(ctx, "tenant_id", ""),
            "release_id": release_id or "",
            "domains": domains,
            "blockers": blockers,
            "decision": decision,
            "generated_at": _now(),
        }
        self._save("product_prr", package)
        return package


__all__ = ["ProductFactoryEnterpriseService", "RELEASE_DOMAINS", "LIFECYCLE_INSTANCE_STATES", "LIFECYCLE_TEMPLATE_PHASES", "WORKFLOW_STATES", "REQUIRED_BLUEPRINT_SECTIONS"]
