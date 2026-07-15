from afritech.novacodepro.completion_standard import (
    PRODUCTION_READY_GATES,
    build_completion_evidence,
    completion_dashboard,
    completion_standard_model,
    evaluate_completion_state,
)


def test_completion_standard_separates_repository_operational_and_governance() -> None:
    standard = completion_standard_model()

    assert standard["levels"] == [
        "Repository Complete",
        "Operationally Verified",
        "Governance Approved",
        "Production Ready",
        "General Availability",
    ]
    assert "Portal UI" in standard["level_1_repository_complete"]["deliverables"]
    assert "Visual regression" in standard["level_2_operationally_verified"]["verifications"]
    assert "Executive" in standard["level_3_governance_approved"]["required_approvals"]
    assert standard["invariants"]["ga_allowed"] is False
    assert standard["invariants"]["real_payments_enabled"] is False


def test_repository_complete_does_not_imply_operational_or_governance_completion() -> None:
    result = evaluate_completion_state(
        repository_complete=True,
        operational_verified=False,
        governance_approved=False,
    )

    assert result["level"] == "Repository Complete"
    assert result["repository_complete"] is True
    assert result["operational_verified"] is False
    assert result["governance_approved"] is False
    assert result["production_ready"] is False
    assert result["ga_allowed"] is False
    assert result["real_payments_enabled"] is False
    assert result["digital_signature"].startswith("sha256:")


def test_production_ready_still_blocks_ga_without_executive_authorization() -> None:
    gates = {gate: True for gate in PRODUCTION_READY_GATES}
    result = evaluate_completion_state(
        repository_complete=True,
        operational_verified=True,
        governance_approved=True,
        production_ready_gates=gates,
        executive_authorized=False,
    )

    assert result["level"] == "Production Ready"
    assert result["production_ready"] is True
    assert result["ga_allowed"] is False
    assert result["missing_production_gates"] == []


def test_general_availability_requires_all_gates_and_executive_authorization() -> None:
    gates = {gate: True for gate in PRODUCTION_READY_GATES}
    result = evaluate_completion_state(
        repository_complete=True,
        operational_verified=True,
        governance_approved=True,
        production_ready_gates=gates,
        executive_authorized=True,
    )

    assert result["level"] == "General Availability"
    assert result["production_ready"] is True
    assert result["ga_allowed"] is True
    assert result["real_payments_enabled"] is False


def test_completion_dashboard_shows_dimension_status_without_single_done_flag() -> None:
    dashboard = completion_dashboard()
    rows = {row["domain"]: row for row in dashboard["rows"]}

    assert dashboard["status"] == "DIMENSIONAL_COMPLETION_DASHBOARD"
    assert rows["UXOS Services"]["repository"] is True
    assert rows["UXOS Services"]["operational"] is False
    assert rows["UXOS Services"]["governance"] == "PENDING"
    assert rows["GA Promotion"]["repository"] is False
    assert dashboard["ga_allowed"] is False


def test_completion_evidence_records_a_signed_audit_shape() -> None:
    evidence = build_completion_evidence(
        {
            "capability": "Visual regression",
            "environment": "production",
            "executor": "NovaCodePro",
            "status": "PASS",
            "artifacts": ["reports/prr/grafana/platform.png"],
            "metrics": {"panel_errors": 0},
            "logs": ["visual-regression.log"],
            "screenshots": ["platform.png"],
            "trace_ids": ["trace-ux-001"],
        },
        evidence_id="ev-ux-001",
    )

    assert evidence["id"] == "ev-ux-001"
    assert evidence["capability"] == "Visual regression"
    assert evidence["metrics"]["panel_errors"] == 0
    assert evidence["digital_signature"].startswith("sha256:")
