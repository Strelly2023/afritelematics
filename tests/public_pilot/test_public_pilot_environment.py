from __future__ import annotations

import json

import pytest

from tests.public_pilot._helpers import (
    PUBLIC_PILOT_APPROVAL_PATH,
    PUBLIC_PILOT_CONFIG_PATH,
    PUBLIC_PILOT_DOWNLOAD_PAGE_PATH,
    PUBLIC_PILOT_EXIT_REPORT_PATH,
    PUBLIC_PILOT_IMPLEMENTATION_PATH,
    PRR_PATH,
    read_json,
    read_text,
)


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_guard]


def test_public_pilot_environment_configuration_exists() -> None:
    config = read_json("config/public_pilot.json")
    assert config["environment"] == "PUBLIC_PILOT"
    assert config["public_users_allowed"] is True
    assert config["invitation_required"] is True
    assert config["approved_regions_only"] is True
    assert config["selected_external_users_allowed"] is True
    assert config["production_infrastructure"] is True
    assert config["pilot_transaction_limits_enabled"] is True
    assert config["pilot_geography_restricted"] is True
    assert config["pilot_monitoring_required"] is True
    assert config["incident_response_required"] is True
    assert config["rollback_required"] is True
    assert config["support_required"] is True
    assert config["ga_enabled"] is False
    assert config["general_availability_allowed"] is False
    assert config["unrestricted_signup_allowed"] is False
    assert config["payment_mode"] == "PILOT_REAL"
    assert config["identity_mode"] == "REAL_WITH_MANUAL_REVIEW"
    assert config["max_transaction_amount_aud"] == 50
    assert config["daily_transaction_limit_aud"] == 200
    assert config["monthly_transaction_limit_aud"] == 1000
    assert config["prr_required"] is True


def test_public_pilot_approval_and_exit_report_are_present() -> None:
    approval = read_json("docs/public_pilot/PUBLIC_PILOT_APPROVAL.json")
    report = read_text("docs/public_pilot/PUBLIC_PILOT_EXIT_REPORT.yaml")
    prr = read_text("docs/prr/PRR-001-production-readiness-review.yaml")
    assert approval["public_pilot_approved"] is True
    assert approval["public_pilot_live_payment_approved"] is False
    assert approval["scope"] == "PUBLIC_PILOT_ONLY"
    assert approval["approved_user_limit"] == 57
    assert len(approval["approved_users"]) == 57
    assert len(approval["approved_devices"]) == 40
    assert "READY_FOR_PRR" in report
    assert "PRODUCTION_READINESS_REVIEW" in prr
    assert "BLOCKED" in prr


def test_public_pilot_docs_exist() -> None:
    for path in (
        PUBLIC_PILOT_CONFIG_PATH,
        PUBLIC_PILOT_APPROVAL_PATH,
        PUBLIC_PILOT_EXIT_REPORT_PATH,
        PUBLIC_PILOT_IMPLEMENTATION_PATH,
        PUBLIC_PILOT_DOWNLOAD_PAGE_PATH,
    ):
        assert path.exists(), path


def test_public_pilot_docs_state_ga_is_blocked() -> None:
    implementation = read_text("docs/public_pilot/PUBLIC_PILOT_IMPLEMENTATION.md")
    download_page = read_text("docs/public_pilot/PUBLIC_PILOT_DOWNLOAD_PAGE.md")
    assert "GA" in implementation
    assert "Public Pilot" in download_page
    assert "production-ready" not in json.dumps(read_json("docs/public_pilot/PUBLIC_PILOT_APPROVAL.json")).lower()
