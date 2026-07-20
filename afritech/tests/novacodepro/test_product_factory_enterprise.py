from __future__ import annotations

from afritech.novacodepro import (
    NovaCodeProPlatform,
    NovaCodeProRepository,
    ProductFactoryEnterpriseService,
    ProductFactoryService,
    build_product_factory_context,
)


class _Claims:
    def __init__(self, *, sub: str = "product-admin", role: str = "ADMIN", tenant_id: str = "novatech") -> None:
        self.sub = sub
        self.role = role
        self.tenant_id = tenant_id
        self.organization_id = tenant_id


def _service(tmp_path):
    repository = NovaCodeProRepository(tmp_path / "novacodepro.sqlite3")
    platform = NovaCodeProPlatform(repository)
    return ProductFactoryService(platform)


def test_product_factory_enterprise_traceability_release_and_prr(tmp_path) -> None:
    service = _service(tmp_path)
    ctx = build_product_factory_context(_Claims())

    request = service.create_request({"product_name": "Factory Product", "status": "Draft"}, ctx)
    blueprint = service.create_blueprint(
        request["id"],
        {
            "vision": "Factory vision",
            "mission": "Factory mission",
            "recommended_architecture": "Platform layer",
            "technology_profile": "Python and React",
            "delivery_strategy": "Iterative",
            "status": "Draft",
        },
        ctx,
    )
    blueprint_version = service.create_blueprint_version(
        blueprint["id"],
        {
            "content": {
                "vision": "Factory vision",
                "mission": "Factory mission",
                "business_problem": "Traceability",
                "market": "Enterprise",
                "users_and_personas": ["Product Manager"],
                "value_proposition": "Governed factory",
                "capabilities": ["requests", "blueprints"],
                "functional_requirements": ["trace links"],
                "non_functional_requirements": ["auditability"],
                "architecture": "NovaCodePro",
                "data_model": "Versioned records",
                "integrations": ["NovaID"],
                "security": ["RBAC"],
                "privacy": ["Tenant isolation"],
                "compliance": ["Audit"],
                "user_experience": ["Accessible"],
                "delivery_strategy": "Iterative",
                "deployment_model": "Controlled",
                "operations": ["Monitoring"],
                "observability": ["Tracing"],
                "resilience": ["Rollback"],
                "release_strategy": ["Commit-bound"],
                "commercial_assumptions": ["Internal platform"],
                "risks": ["Scope creep"],
                "exclusions": ["Public GA"],
                "dependencies": ["NovaID"],
                "acceptance_criteria": ["Approved"],
            }
        },
        ctx,
    )
    approved_version = service.approve_blueprint_version(blueprint["id"], blueprint_version["id"], ctx)
    assert approved_version["status"] == "Approved"
    amended_version = service.amend_blueprint_version(blueprint["id"], blueprint_version["id"], {"delivery_strategy": "Controlled rollout"}, ctx)
    assert amended_version["parent_version"] == blueprint_version["id"]
    assert amended_version["id"] != blueprint_version["id"]

    requirement = service.create_requirement(
        {
            "product_id": "product-factory",
            "blueprint_id": blueprint["id"],
            "blueprint_version_id": blueprint_version["id"],
            "title": "Traceability requirement",
            "statement": "Maintain governed traceability",
            "mandatory_for_ga": True,
            "class": "Functional",
            "implementation_links": ["impl-1"],
            "test_links": ["test-1"],
            "evidence_links": ["evidence-1"],
            "release_links": ["release-1"],
        },
        ctx,
    )
    link = service.create_traceability_link(
        {
            "source_entity_type": "requirement",
            "source_entity_id": requirement["id"],
            "target_entity_type": "blueprint",
            "target_entity_id": blueprint["id"],
            "relationship_type": "supports",
            "status": "DRAFT",
            "provenance": "test",
            "evidence": [blueprint["id"]],
        },
        ctx,
    )
    assert service.traceability_validate(ctx)["status"] == "COMPLETE"
    assert service.traceability_coverage(ctx)["requirements"] >= 1
    assert service.traceability_gaps(ctx)["count"] == 0
    assert service.delete_traceability_link(link["id"], ctx) == {"deleted": True, "id": link["id"]}

    lifecycle_template = service.create_lifecycle_template({"name": "Factory lifecycle"}, ctx)
    lifecycle = service.create_lifecycle(request["id"], {"template_id": lifecycle_template["id"]}, ctx)
    assert service.start_lifecycle(lifecycle["id"], ctx)["status"] == "Ready"
    assert service.lifecycle_readiness(lifecycle["id"], ctx)["domains"]

    workflow_definition = service.create_workflow_definition({"name": "Release workflow", "steps": ["review", "approve"], "roles": ["ADMIN"], "approvals": ["manager"]}, ctx)
    workflow_instance = service.create_workflow_instance({"definition_id": workflow_definition["id"], "product_id": "product-factory"}, ctx)
    assert service.transition_workflow_instance(workflow_instance["id"], {"state": "Running", "version": 1}, ctx)["state"] == "Running"
    assert service.approve_workflow_instance(workflow_instance["id"], ctx)["state"] == "Completed"

    release = service.create_release({"product_id": "product-factory", "name": "Factory release"}, ctx)
    release = service.register_release_candidate(release["id"], {"candidate_id": blueprint_version["id"], "commit_sha": "commit-1", "blueprint_version_id": blueprint_version["id"]}, ctx)
    service.register_release_evidence(release["id"], {"artifact_id": "evidence-1"}, ctx)
    service.create_release_approval(release["id"], {"decision": "APPROVED", "role": "ADMIN"}, ctx)
    evaluated = service.evaluate_release(release["id"], ctx)
    assert evaluated["status"] == "Ready"
    assert service.release_decision(release["id"], {"decision": "APPROVED"}, ctx)["status"] == "Approved"
    prr = service.prr(ctx, release["id"])
    assert prr["decision"] == "APPROVED"

    assert service.search(ctx, {"query": "traceability"})["count"] >= 1
    assert service.reports_catalog()["reports"]
    assert service.run_report(ctx, {"report_id": "product-portfolio"})["report"]["report_id"] == "product-portfolio"
    assert service.dashboard(ctx, "quality")["kind"] == "quality"
    assert service.cross_product_relationships(ctx, {"source_product": "product-factory", "target_product": "novaid"})["source_product"] == "product-factory"
    assert service.cross_product_validate(ctx)["status"] == "PASS"

    migration = service.create_migration({"product_id": "product-factory", "source_system": "legacy", "target_system": "factory"}, ctx)
    assert service.assess_migration(migration["id"], ctx)["status"] == "Assessed"
    assert service.map_migration(migration["id"], ctx)["status"] == "Mapped"
    preview = service.preview_migration(migration["id"], ctx)
    assert preview["migration"]["id"] == migration["id"]
    assert service.approve_migration(migration["id"], ctx)["status"] == "Approved"
    assert service.execute_migration(migration["id"], ctx)["status"] == "Running"
    assert service.validate_migration(migration["id"], ctx)["result"] == "BLOCKED"
    assert service.reconcile_migration(migration["id"], ctx)["status"] == "Reconciled"
    assert service.rollback_migration(migration["id"], ctx)["status"] == "Rolled Back"

    assert service.prr(ctx, release["id"])["release_id"] == release["id"]


def test_product_factory_enterprise_rejects_approved_trace_links(tmp_path) -> None:
    service = _service(tmp_path)
    ctx = build_product_factory_context(_Claims())
    request = service.create_request({"product_name": "Factory Product", "status": "Draft"}, ctx)
    blueprint = service.create_blueprint(request["id"], {"vision": "v", "mission": "m", "recommended_architecture": "a", "technology_profile": "t", "delivery_strategy": "d", "status": "Draft"}, ctx)
    requirement = service.create_requirement({"product_id": "product-factory", "blueprint_id": blueprint["id"], "title": "Trace", "statement": "Trace", "mandatory_for_ga": True, "class": "Functional"}, ctx)
    link = service.create_traceability_link(
        {
            "source_entity_type": "requirement",
            "source_entity_id": requirement["id"],
            "target_entity_type": "blueprint",
            "target_entity_id": blueprint["id"],
            "status": "DRAFT",
        },
        ctx,
    )
    link["status"] = "APPROVED"
    service.platform.repository.upsert("product_traceability_link", link)
    try:
        service.delete_traceability_link(link["id"], ctx)
    except Exception as exc:  # noqa: BLE001
        assert "superseded" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected approved link deletion to fail")
