import copy

import pytest
import yaml

from afritech.ci.epoch_lifecycle_validator import (
    EPOCH_LIFECYCLE_REGISTRY,
    REPLAY_TRANSLATOR_REGISTRY,
    EpochLifecycleValidationError,
    validate,
    validate_epoch_lifecycle_payload,
    validate_translator_registry_payload,
)


def load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_epoch_lifecycle_validator_passes_current_registries():
    validate()


def test_epoch_lifecycle_rejects_missing_interface_version():
    payload = load_yaml(EPOCH_LIFECYCLE_REGISTRY)
    broken = copy.deepcopy(payload)
    del broken["epochs"]["EPOCH-1"]["interface_versions"]["replay"]

    with pytest.raises(EpochLifecycleValidationError):
        validate_epoch_lifecycle_payload(broken)


def test_epoch_lifecycle_rejects_retired_epoch_without_retirement_eligibility():
    payload = load_yaml(EPOCH_LIFECYCLE_REGISTRY)
    broken = copy.deepcopy(payload)
    broken["epochs"]["EPOCH-1"]["status"] = "RETIRED"
    broken["epochs"]["EPOCH-1"]["retirement"]["eligible"] = False

    with pytest.raises(EpochLifecycleValidationError):
        validate_epoch_lifecycle_payload(broken)


def test_translator_registry_accepts_empty_translator_set():
    payload = load_yaml(REPLAY_TRANSLATOR_REGISTRY)

    validate_translator_registry_payload(payload)


def test_translator_registry_rejects_active_translator_without_passing_fixtures():
    payload = load_yaml(REPLAY_TRANSLATOR_REGISTRY)
    broken = copy.deepcopy(payload)
    broken["translators"]["T-EPOCH-0-REPLAY"] = {
        "status": "ACTIVE",
        "source_epoch": "EPOCH-0",
        "target_interface": "replay.v1",
        "compatibility_class": "C",
        "fixture_status": "MISSING",
        "owner": "constitutional-core",
        "retirement_path": "archive_after_trace_population_zero",
    }

    with pytest.raises(EpochLifecycleValidationError):
        validate_translator_registry_payload(broken)


def test_translator_registry_enforces_default_budget():
    payload = load_yaml(REPLAY_TRANSLATOR_REGISTRY)
    broken = copy.deepcopy(payload)
    broken["translators"] = {
        "T1": {
            "status": "STABLE",
            "source_epoch": "EPOCH-0",
            "target_interface": "replay.v1",
            "compatibility_class": "C",
            "fixture_status": "PASSING",
            "owner": "constitutional-core",
            "retirement_path": "archive_after_trace_population_zero",
        },
        "T2": {
            "status": "STABLE",
            "source_epoch": "EPOCH-0",
            "target_interface": "replay.v1",
            "compatibility_class": "C",
            "fixture_status": "PASSING",
            "owner": "constitutional-core",
            "retirement_path": "archive_after_trace_population_zero",
        },
    }

    with pytest.raises(EpochLifecycleValidationError):
        validate_translator_registry_payload(broken)


def test_translator_registry_allows_budget_exception():
    payload = load_yaml(REPLAY_TRANSLATOR_REGISTRY)
    allowed = copy.deepcopy(payload)
    allowed["translators"] = {
        "T1": {
            "status": "STABLE",
            "source_epoch": "EPOCH-0",
            "target_interface": "replay.v1",
            "compatibility_class": "C",
            "fixture_status": "PASSING",
            "owner": "constitutional-core",
            "retirement_path": "archive_after_trace_population_zero",
        },
        "T2": {
            "status": "STABLE",
            "source_epoch": "EPOCH-0",
            "target_interface": "replay.v1",
            "compatibility_class": "C",
            "fixture_status": "PASSING",
            "owner": "constitutional-core",
            "retirement_path": "archive_after_trace_population_zero",
        },
    }
    allowed["exceptions"] = {
        "EX-001": {
            "source_epoch": "EPOCH-0",
            "target_interface": "replay.v1",
            "approved": True,
            "reason": "temporary historical replay split",
        }
    }

    validate_translator_registry_payload(allowed)
