from __future__ import annotations

from afritech.novacodepro.ux_operating_system import (
    assess_ux_release_readiness,
    ai_design_studio_model,
    build_ux_artifact_record,
    build_ux_evidence_package,
    build_uxos_service_record,
    component_registry_model,
    digital_ux_twin_model,
    enterprise_design_knowledge_graph_model,
    sign_ux_record,
    ux_operating_system_summary,
    ux_studio_registry,
    ux_validation_model,
    uxos_operational_completion_matrix,
    uxos_service_architecture,
    validate_ux_state_transition,
)


def test_ux_operating_system_models_design_to_operations_lifecycle() -> None:
    summary = ux_operating_system_summary()

    assert summary["name"] == "NovaCodePro Enterprise UX Operating System"
    assert summary["status"] == "IMPLEMENTED_NOT_PRODUCTION_APPROVED"
    assert summary["governance"]["ga_allowed"] is False
    assert summary["lifecycle"][0] == "Business Strategy"
    assert summary["lifecycle"][-1] == "Continuous Optimization"
    assert "Production Readiness Review" in summary["lifecycle"]
    assert "Executive Approval" in summary["lifecycle"]


def test_ux_state_model_preserves_prr_executive_and_ga_boundaries() -> None:
    states = ux_operating_system_summary()["state_model"]

    assert states.index("READY_FOR_PRR_APPROVAL") < states.index("PRR_APPROVED")
    assert states.index("PRR_APPROVED") < states.index("EXECUTIVE_APPROVED")
    assert states.index("EXECUTIVE_APPROVED") < states.index("GENERAL_AVAILABILITY")


def test_ux_studios_own_artifacts_approvals_metrics_and_evidence() -> None:
    registry = ux_studio_registry()

    assert registry["status"] == "ENTERPRISE_UX_STUDIOS_DEFINED"
    studios = {studio["name"]: studio for studio in registry["studios"]}
    for name in (
        "Requirements Studio",
        "Research Studio",
        "Journey Studio",
        "Wireframe Studio",
        "Prototype Studio",
        "Design System Studio",
        "Accessibility Studio",
        "Localization Studio",
        "Motion Studio",
        "Handoff Center",
        "Verification Center",
        "UX Governance Center",
    ):
        assert name in studios
        assert "approvals" in studios[name]
        assert "evidence" in studios[name]
        assert "metrics" in studios[name]


def test_component_ai_and_validation_models_are_governed() -> None:
    components = component_registry_model()
    assert components["status"] == "ENTERPRISE_COMPONENT_ASSET_MODEL"
    assert "Buttons" in components["components"]
    assert components["schema"]["accessibility"] == "required"
    assert components["schema"]["performance"] == "required"

    ai = ai_design_studio_model()
    assert ai["status"] == "AI_ASSISTED_HUMAN_GOVERNED"
    assert "Voice Description" in ai["inputs"]
    assert "Accessibility Agent" in ai["agents"]
    assert "human reviewers" in ai["authority_boundary"]

    validation = ux_validation_model()
    assert validation["accessibility"]["evidence_schema"]["wcag_level"] == "AA"
    assert "Offline Behavior" in validation["verification"]["checks"]
    assert "A/B Testing" in validation["experiments"]


def test_ux_artifacts_are_signed_versioned_and_evidence_backed() -> None:
    artifact = build_ux_artifact_record(
        {
            "artifact": "Booking prototype",
            "artifact_type": "prototype",
            "studio": "Prototype Studio",
            "version": "v3",
            "traceability": {"requirement_id": "req-1", "prototype_id": "proto-1"},
            "evidence": ["prototype-validation.yaml"],
        },
        "2026-07-15T00:00:00Z",
        "uxart-1",
    )
    signed = sign_ux_record(artifact)
    evidence_package = build_ux_evidence_package(signed, signed["evidence"], "2026-07-15T00:00:00Z", "uxevidence-1")

    assert signed["version"] == "v3"
    assert signed["digital_signature"].startswith("sha256:")
    assert evidence_package["status"] == "EVIDENCE_CAPTURED"
    assert evidence_package["digital_signature"].startswith("sha256:")


def test_ux_state_transition_prevents_skipped_or_backward_states() -> None:
    assert validate_ux_state_transition("DRAFT", "RESEARCH_COMPLETE")["valid"] is True
    assert validate_ux_state_transition("DRAFT", "IA_APPROVED")["valid"] is False
    assert validate_ux_state_transition("IA_APPROVED", "RESEARCH_COMPLETE")["valid"] is False


def test_ux_release_readiness_requires_traceability_and_approvals_without_ga() -> None:
    assessment = assess_ux_release_readiness(
        [
            {
                "id": "uxart-1",
                "artifact": "Requirement",
                "artifact_type": "requirement",
                "approval_state": "IMPLEMENTATION_VERIFIED",
                "traceability": {},
            }
        ]
    )

    assert assessment["status"] == "EVIDENCE_PENDING"
    assert assessment["complete"] is False
    assert assessment["ga_allowed"] is False
    assert assessment["missing_artifacts"] == ["prototype", "accessibility_review", "implementation_verification"]


def test_uxos_runtime_services_are_architecturally_implemented_but_evidence_pending() -> None:
    services = uxos_service_architecture()
    completion = uxos_operational_completion_matrix()

    assert services["status"] == "SERVICES_IMPLEMENTED_LIVE_INTEGRATION_PENDING"
    assert "Figma" in services["design_integration_fabric"]["providers"]
    assert "Chrome" in services["visual_regression"]["browsers"]
    assert "WCAG 2.2 AA" in services["accessibility_automation"]["checks"]
    assert "A/B Testing" in services["experimentation"]["capabilities"]
    assert completion["repository_implementation_complete"] is True
    assert completion["operational_complete"] is False
    assert completion["ga_allowed"] is False
    assert completion["real_payments_enabled"] is False


def test_uxos_graph_twin_and_service_records_are_signed_and_not_operationally_complete() -> None:
    graph = enterprise_design_knowledge_graph_model()
    twin = digital_ux_twin_model()
    record = build_uxos_service_record(
        "ux_visual_regression",
        {
            "subject": "Driver dashboard baseline",
            "provider": "Chrome",
            "environment": "ci",
            "evidence_refs": ["reports/ux/visual/driver-dashboard.yaml"],
        },
        "2026-07-15T00:00:00Z",
        "uxos-1",
    )

    assert graph["lineage"][0] == "Requirement"
    assert "Affected Evidence" in graph["impact_analysis"]
    assert "Poor network" in twin["simulation_scenarios"]
    assert record["digital_signature"].startswith("sha256:")
    assert record["operational_complete"] is False
    assert record["ga_allowed"] is False
