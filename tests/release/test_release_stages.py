from __future__ import annotations

import pytest

from tests.release._helpers import CONFIG_PATH, DOC_PATH, READINESS_SOURCE, RELEASE_STAGE_SOURCE, read_json, read_text


pytestmark = [pytest.mark.release, pytest.mark.governance]


def test_release_stage_configuration_is_canonical() -> None:
    config = read_json(CONFIG_PATH)
    assert config["releaseStage"] == "PUBLIC_PILOT"
    assert config["gaEnabled"] is False
    assert config["prrRequired"] is True
    assert config["paymentMode"] == "PILOT_REAL_LIMITED"
    assert config["productionRealPaymentMode"] == "disabled"


def test_release_stage_source_defines_all_canonical_stages() -> None:
    source = read_text(RELEASE_STAGE_SOURCE)
    for stage in (
        "PRIVATE_DEVELOPMENT",
        "INTERNAL_QA",
        "CONTROLLED_PILOT",
        "PUBLIC_PILOT",
        "PRODUCTION_READINESS_REVIEW",
        "GENERAL_AVAILABILITY",
        "REGIONAL_EXPANSION",
        "GLOBAL_MULTI_REGION_PLATFORM",
    ):
        assert stage in source
    for phrase in ("allowedPaymentModes", "requiredGovernanceArtifacts", "allowedActivationGates"):
        assert phrase in source


def test_release_framework_doc_exists() -> None:
    doc = read_text(DOC_PATH)
    for phrase in (
        "Release Stages",
        "Activation Gates",
        "Readiness Domains",
        "GA may be enabled only after PRR is explicitly approved",
        "NovaAI remains advisory only",
    ):
        assert phrase in doc


def test_readiness_source_lists_all_domains() -> None:
    source = read_text(READINESS_SOURCE)
    for domain in ("Engineering", "Operations", "Governance", "Compliance", "Commercial", "Security", "Support", "DisasterRecovery"):
        assert domain in source

