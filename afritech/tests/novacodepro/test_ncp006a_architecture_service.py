from __future__ import annotations

from pathlib import Path

from afritech.novacodepro import NovaCodeProRepository
from afritech.novacodepro.ncp006a import ArchitectureError, ArchitectureExecutionContext, NovaCodeProNCP006AService


def _ctx(*, workspace_id: str | None = "architecture-workspace", role: str = "ARCHITECT", permissions: tuple[str, ...] = ("architecture.read", "architecture.create", "architecture.update", "architecture.review", "architecture.approve", "architecture.baseline", "architecture.validate", "architecture.traceability")) -> ArchitectureExecutionContext:
    return ArchitectureExecutionContext(
        actor_id="arch.user",
        tenant_id="novatech",
        organization_id="novatech",
        workspace_id=workspace_id,
        project_id="project-1",
        request_id="request-1",
        role=role,
        permissions=permissions,
        session_id="session-1",
        correlation_id="corr-1",
    )


def test_ncp006a_service_architecture_graph_validation_and_baselines(tmp_path: Path) -> None:
    repository = NovaCodeProRepository(tmp_path / "novacodepro.sqlite3")
    service = NovaCodeProNCP006AService(repository)
    workspace_ctx = _ctx()

    workspace = service.create_workspace({"name": "Enterprise Architecture", "domain": "ENTERPRISE"}, workspace_ctx)
    model_ctx = _ctx(workspace_id=workspace["id"])
    model = service.create_model({"workspace_id": workspace["id"], "name": "Platform Architecture", "domain": "SOLUTION"}, model_ctx)

    component = service.create_component({"model_id": model["id"], "name": "API Gateway", "component_type": "GATEWAY"}, model_ctx)
    relationship = service.add_relationship({"model_id": model["id"], "source_id": model["id"], "target_id": component["id"], "relationship": "CONTAINS"}, model_ctx)
    assert relationship["relationship"] == "CONTAINS"

    review = service.create_review(model["id"], {"review_type": "ARCHITECTURE", "required_role": "ARCHITECT"}, model_ctx)
    completed = service.complete_review(model["id"], review["id"], {"decision": "APPROVED", "findings": ["approved"]}, model_ctx)
    assert completed["decision"] == "APPROVED"

    approval = service.request_approval(model["id"], {"required_role": "ARCHITECT", "risk_class": "HIGH"}, model_ctx)
    decided = service.decide_approval(model["id"], approval["id"], {"decision": "APPROVED", "reason": "approved"}, model_ctx)
    assert decided["decision"] == "APPROVED"

    baseline = service.create_baseline(model["id"], {"name": "Baseline A", "approval_references": [approval["id"]]}, model_ctx)
    assert baseline["status"] == "APPROVED"
    activated = service.activate_baseline(model["id"], baseline["id"], model_ctx)
    assert activated["status"] == "ACTIVE"

    trace_link = service.create_traceability_link(
        {
            "source_type": "ARCHITECTURE_MODEL",
            "source_id": model["id"],
            "target_type": "ARCHITECTURE_COMPONENT",
            "target_id": component["id"],
            "relationship": "DERIVED_FROM",
        },
        model_ctx,
    )
    assert trace_link["relationship"] == "DERIVED_FROM"

    coverage = service.calculate_traceability_coverage(model_ctx, model_id=model["id"])
    assert coverage["coverage"]["coverage_ratio"] >= 0
    assert coverage["gaps"] == []
    validation = service.validate_model(model["id"], {"validation_type": "DEPENDENCY"}, model_ctx)
    assert validation["status"] in {"PASS", "FAIL"}
    impact = service.calculate_impact(model["id"], model_ctx)
    assert impact["status"] in {"ACTIVE", "NO_IMPACT"}


def test_ncp006a_service_rejects_cross_tenant_access(tmp_path: Path) -> None:
    repository = NovaCodeProRepository(tmp_path / "novacodepro.sqlite3")
    service = NovaCodeProNCP006AService(repository)
    ctx = _ctx()
    workspace = service.create_workspace({"name": "Enterprise Architecture"}, ctx)
    model_ctx = _ctx(workspace_id=workspace["id"])
    model = service.create_model({"workspace_id": workspace["id"], "name": "Platform Architecture"}, model_ctx)

    forbidden_ctx = _ctx(workspace_id=workspace["id"], permissions=("architecture.read",), role="ARCHITECT")
    forbidden_ctx = ArchitectureExecutionContext(
        actor_id="arch.other",
        tenant_id="foreign-tenant",
        organization_id="foreign-tenant",
        workspace_id=workspace["id"],
        project_id=None,
        request_id=None,
        role="ARCHITECT",
        permissions=("architecture.read",),
        session_id="session-2",
        correlation_id="corr-2",
    )

    try:
        service.get_model(model["id"], forbidden_ctx)
    except ArchitectureError as error:
        assert error.code == "cross_tenant_architecture_forbidden"
    else:  # pragma: no cover - safety
        raise AssertionError("expected cross-tenant access to be forbidden")
