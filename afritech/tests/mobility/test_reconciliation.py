from __future__ import annotations

from copy import deepcopy

import pytest

from afritech.mobility.reconciliation import (
    SimulationRealityReconciliationError,
    reconcile_simulation_and_reality,
    validate_reconciliation_report,
)
from afritech.mobility.field_evidence import ingest_field_evidence_signals
from afritech.simulation.pilot_dataset import (
    generate_airport_pilot_dataset,
    generate_airport_pilot_dispatches,
    generate_airport_pilot_ingestions,
    generate_airport_pilot_signals,
)


def test_airport_reconciliation_is_aligned():
    simulation = generate_airport_pilot_dataset()
    live_results = generate_airport_pilot_ingestions()
    report = reconcile_simulation_and_reality(simulation, live_results)

    assert report.aligned is True
    assert report.divergence_count == 0
    assert report.divergence_score == 0.0
    assert report.recommendation == "continue"
    assert validate_reconciliation_report(report) is True


def test_airport_reconciliation_detects_divergence():
    simulation = generate_airport_pilot_dataset()
    dispatch = generate_airport_pilot_dispatches()[0]
    signals = [deepcopy(signal) for signal in generate_airport_pilot_signals()[0]]
    signals[0]["payload"]["shadow_note"] = "delayed airport taxi"  # type: ignore[index]
    live_result = ingest_field_evidence_signals(dispatch, signals)

    report = reconcile_simulation_and_reality(simulation, (live_result,))

    assert report.aligned is False
    assert report.divergence_count > 0
    assert report.recommendation in {
        "continue_with_monitoring",
        "shadow_more",
        "investigate",
        "stop",
    }


def test_reconciliation_rejects_non_simulation_input():
    with pytest.raises(SimulationRealityReconciliationError):
        reconcile_simulation_and_reality({}, ())  # type: ignore[arg-type]
