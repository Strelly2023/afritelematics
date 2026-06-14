from __future__ import annotations

import pytest

from afritech.simulation.pilot_dataset import (
    AUTHORITY_BOUNDARY,
    SCENARIO_AUTHORITY_BOUNDARY,
    PilotDatasetSimulationError,
    generate_airport_pilot_dataset,
)


def test_airport_pilot_dataset_is_deterministic():
    first = generate_airport_pilot_dataset()
    second = generate_airport_pilot_dataset()

    assert first.verified is True
    assert first.dataset_hash == second.dataset_hash
    assert first.canonical_dict() == second.canonical_dict()


def test_airport_pilot_dataset_defines_first_live_deployment_scenario():
    dataset = generate_airport_pilot_dataset()
    scenario = dataset.scenario

    assert scenario["scenario_id"] == "airport-zone-001"
    assert scenario["deployment_type"] == "airport"
    assert scenario["zone"] == "airport_pickup_dropoff_zone"
    assert scenario["authority_boundary"] == SCENARIO_AUTHORITY_BOUNDARY
    assert scenario["live_money"] == "disabled_by_default"
    assert "adr_0042_runtime_validation" in scenario["required_gates"]
    assert "unapproved_live_money_movement" in scenario["stop_conditions"]


def test_airport_pilot_dataset_generates_reality_integrated_operations():
    dataset = generate_airport_pilot_dataset(operation_count=4)

    assert dataset.authority_boundary == AUTHORITY_BOUNDARY
    assert len(dataset.operations) == 4
    assert {operation.signal_count for operation in dataset.operations} == {7}
    assert all(len(operation.collection_hash) == 64 for operation in dataset.operations)
    assert all(len(operation.proof_hash) == 64 for operation in dataset.operations)
    assert all(len(operation.ingestion_hash) == 64 for operation in dataset.operations)


def test_airport_pilot_dataset_rejects_empty_operation_count():
    with pytest.raises(PilotDatasetSimulationError):
        generate_airport_pilot_dataset(operation_count=0)
