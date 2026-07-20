from __future__ import annotations

from afritech.novacodepro import (
    NovaCodeProPlatform,
    NovaCodeProRepository,
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


def test_product_factory_service_lifecycle(tmp_path) -> None:
    service = _service(tmp_path)
    ctx = build_product_factory_context(_Claims())

    request = service.create_request({"product_name": "NovaFactory", "status": "Draft"}, ctx)
    blueprint = service.create_blueprint(
        request["id"],
        {
            "vision": "A governed factory",
            "mission": "Move from idea to production",
            "recommended_architecture": "Platform layer",
            "technology_profile": "Python and React",
            "delivery_strategy": "Iterative",
            "status": "Draft",
        },
        ctx,
    )
    approved_blueprint = service.approve_blueprint(blueprint["id"], ctx, evidence=[blueprint["id"]])
    assert approved_blueprint["status"] == "Approved"

    phases = service.phases(ctx)
    phase = service.transition_phase(phases[0]["id"], "Ready", ctx, note="Prepared")
    assert phase["status"] == "Ready"

    evidence = service.create_evidence({"title": "Blueprint evidence", "type": "artifact", "subject": blueprint["id"], "blueprint_id": blueprint["id"]}, ctx)
    assert evidence["result"] == "PASS"

    gate = service.create_gate_decision({"name": "Blueprint gate", "decision": "Approved", "phase_id": phase["id"], "linked_commit": "commit-1"}, ctx)
    assert gate["decision"] == "Approved"

    improvement = service.create_improvement({"title": "Improve traceability", "priority": "high"}, ctx)
    assert improvement["title"] == "Improve traceability"

    traceability = service.traceability_matrix(ctx)
    assert traceability["coverage"]["requirements"] >= 1
    assert service.overview(ctx)["summary"]["requests"] >= 1
    assert service.demo_product(ctx)["name"] in {"NovaFactory Demo", "NovaFactory"}


def test_product_factory_rejects_invalid_transitions_and_status(tmp_path) -> None:
    service = _service(tmp_path)
    ctx = build_product_factory_context(_Claims())
    request = service.create_request({"product_name": "NovaFactory", "status": "Draft"}, ctx)

    try:
        service.transition_request(request["id"], "Approved", ctx)
    except Exception as exc:  # noqa: BLE001
        assert getattr(exc, "code", "") in {"invalid_request_transition", "request_not_found"}
    else:  # pragma: no cover - defensive
        raise AssertionError("expected transition failure")

    try:
        service.create_request({"product_name": "Bad", "status": "NotAState"}, ctx)
    except Exception as exc:  # noqa: BLE001
        assert getattr(exc, "code", "") == "invalid_status"
    else:  # pragma: no cover - defensive
        raise AssertionError("expected invalid status failure")
