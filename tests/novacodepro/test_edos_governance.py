from __future__ import annotations

from afritech.novacodepro.edos import (
    CertificationState,
    authority_model,
    backend_service_architecture,
    capability_state_registry,
    continuous_compliance_model,
    edos_maturity_report,
    edos_summary,
    enterprise_readiness_matrix,
    frontend_experience_registry,
    infrastructure_certification_records,
    mobile_release_certificate,
    prr_governance_workflow,
    validate_certification_state,
)


def test_edos_keeps_implemented_verified_certified_approved_separate() -> None:
    summary = edos_summary()

    assert summary["classification"] == "IMPLEMENTED_NOT_PRODUCTION_APPROVED"
    assert summary["runtime_certification"]["implemented"] == 10
    assert summary["runtime_certification"]["verified"] == 0
    assert summary["runtime_certification"]["certified"] == 0
    assert summary["runtime_certification"]["approved"] == 0
    assert summary["governance_state"]["GA_ALLOWED"] is False
    assert summary["governance_state"]["REAL_PAYMENTS_ENABLED"] is False
    assert summary["capability_model"]["lifecycle"][6] == "Certification"
    assert summary["capability_states"]["status"] == "FOUR_STATE_GOVERNANCE_MODEL"
    assert summary["frontend_experiences"]["status"] == "FEDERATED_EXPERIENCE_LAYER"
    assert summary["backend_services"]["status"] == "FEDERATED_DOMAIN_SEPARATED_BACKENDS"
    assert summary["authority_model"]["status"] == "AUTHORITY_SEPARATION_ENFORCED"
    assert summary["continuous_compliance"]["active"] is False
    assert summary["readiness_matrix"]["status"] == "STATE_BASED_READINESS"


def test_live_infrastructure_records_do_not_claim_verification_without_evidence() -> None:
    records = infrastructure_certification_records()

    assert {record["component"] for record in records} >= {"PostgreSQL", "Runtime Worker", "Replay Worker", "OpenTelemetry"}
    assert all(record["state"]["implemented"] is True for record in records)
    assert all(record["state"]["verified"] is False for record in records)
    assert all(record["state"]["certified"] is False for record in records)
    assert all(record["state"]["approved"] is False for record in records)


def test_certification_state_validation_prevents_skipped_lifecycle_stages() -> None:
    assert validate_certification_state(CertificationState(implemented=True, verified=True, certified=True)).to_dict() == {
        "valid": True,
        "current_state": "certified",
        "issues": [],
    }

    invalid = validate_certification_state(CertificationState(implemented=True, verified=False, certified=True, approved=True))
    assert invalid.valid is False
    assert invalid.current_state == "approved"
    assert invalid.issues == ("certified_requires_verified",)


def test_capability_state_registry_tracks_exactly_one_ordered_model_per_domain() -> None:
    registry = capability_state_registry()

    assert registry["states"] == ["implemented", "verified", "certified", "approved"]
    records = registry["records"]
    assert {record["domain"] for record in records} >= {"Runtime Platform", "Evidence Platform", "GA Governance"}
    assert all(record["lifecycle_validation"]["valid"] is True for record in records)
    assert {record["lifecycle_validation"]["current_state"] for record in records} >= {
        "implemented",
        "certified",
        "approved",
    }


def test_frontend_registry_is_role_federated_with_shared_governance() -> None:
    registry = frontend_experience_registry()

    assert registry["principle"] == "One platform foundation, multiple role-specific workspaces, one governed source of truth."
    names = {experience["name"] for experience in registry["experiences"]}
    assert {
        "NovaCodePro Workspace",
        "NovaCodePro Developer",
        "NovaCodePro Operations",
        "NovaCodePro Evidence",
        "NovaCodePro PRR Center",
        "NovaCodePro GA Governance",
        "NovaCodePro CLI",
    }.issubset(names)
    ga = next(experience for experience in registry["experiences"] if experience["name"] == "NovaCodePro GA Governance")
    assert "may not self-approve GA" in ga["authority_boundary"]
    assert "Backend enforcement" in registry["security_model"]
    assert "Release Certification" in registry["quality_gates"]


def test_backend_architecture_is_domain_separated_and_event_governed() -> None:
    architecture = backend_service_architecture()

    names = {service["name"] for service in architecture["services"]}
    assert {
        "API Gateway and Edge Backend",
        "Requirements Backend",
        "Architecture Backend",
        "Release Backend",
        "Replay Backend",
        "Evidence Backend",
        "PRR Backend",
        "GA Governance Backend",
    }.issubset(names)
    assert "No service writes directly to another service database." in architecture["data_rules"]
    assert "Transactional outbox" in architecture["reliability_controls"]
    assert "integrity_hash" in architecture["event_contract"]
    release = next(service for service in architecture["services"] if service["name"] == "Release Backend")
    assert release["authority_boundary"] == "Implemented != verified; verified != certified; certified != approved; approved != deployed; deployed != GA."


def test_authority_model_keeps_novacodepro_from_owning_final_approvals() -> None:
    model = authority_model()

    assert "GA approval" in model["non_delegable_decisions"]
    assert "real payment activation" in model["non_delegable_decisions"]
    assert "signed evidence" in model["authorities"]["NovaTrust"]
    assert "financial execution" in model["authorities"]["NovaPay"]
    assert "advisory analysis" in model["authorities"]["NovaAI"]


def test_mobile_release_certificate_preserves_device_and_approval_pending() -> None:
    certificate = mobile_release_certificate()

    assert certificate["status"] == "CERTIFICATION_PENDING_DEVICE_AND_APPROVAL"
    assert certificate["release"] == {"product": "NovaRide", "application": "Driver", "version": "2026.1.4"}
    assert certificate["build"]["passed"] is True
    assert certificate["tests"]["passed"] is True
    assert certificate["device"]["certified"] is False
    assert certificate["approved"] is False


def test_prr_blocks_ga_until_all_reviews_approved() -> None:
    prr = prr_governance_workflow()

    assert prr["status"] == "PRR_PENDING"
    assert prr["ga_allowed"] is False
    assert len(prr["reviews"]) == 6
    assert all(review["approval_status"] == "PENDING" for review in prr["reviews"])
    assert all(review["digital_signature"] is None for review in prr["reviews"])


def test_maturity_report_distinguishes_enterprise_grade_from_production_certification() -> None:
    report = edos_maturity_report()

    assert report["domains"]["Architecture"] == 10
    assert report["domains"]["Engineering"] == 10
    assert report["production_verification"] == "PENDING_LIVE_EVIDENCE"
    assert report["prr_approval"] == "PENDING_GOVERNANCE_REVIEW"
    assert report["ga_approval"] == "PENDING"


def test_operational_evidence_artifacts_require_hash_timestamp_and_reviewer() -> None:
    evidence = edos_summary()["operational_evidence"]

    names = {artifact["name"] for artifact in evidence["artifacts"]}
    assert {"Backup", "Restore", "Replay", "Runtime Verification", "PRR Evidence"}.issubset(names)
    for artifact in evidence["artifacts"]:
        assert artifact["immutable"] is True
        assert "timestamp" in artifact
        assert "hash" in artifact
        assert "reviewer_identity" in artifact
        assert "digital_signature" in artifact


def test_readiness_matrix_reports_state_not_single_score() -> None:
    matrix = enterprise_readiness_matrix()

    rows = {row["domain"]: row for row in matrix["rows"]}
    assert rows["Requirements"]["Approval"] is True
    assert rows["Runtime Platform"]["Runtime Verification"] == "PENDING"
    assert rows["GA"]["Approval"] == "PENDING"


def test_continuous_compliance_is_defined_but_not_active_before_ga() -> None:
    model = continuous_compliance_model()

    assert model["post_ga_loop"][0] == "Production"
    assert "Evidence Refresh" in model["post_ga_loop"]
    assert model["active"] is False
