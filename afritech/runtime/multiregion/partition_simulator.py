"""Region partition and locality scenarios."""

from __future__ import annotations

from typing import Any, Mapping

from afritech.runtime.multiregion.region_model import RegionView


def partition_regions(
    scenario: str,
    baseline_trace: tuple[Mapping[str, Any], ...],
) -> tuple[RegionView, ...]:
    if scenario == "full_partition":
        return (
            RegionView("region_A", (baseline_trace[0], baseline_trace[1])),
            RegionView("region_B", baseline_trace[2:5]),
            RegionView("region_C", baseline_trace[5:]),
        )
    if scenario == "conflicting_local_order":
        return (
            RegionView("region_A", baseline_trace),
            RegionView("region_B", (baseline_trace[3], baseline_trace[0], baseline_trace[2], baseline_trace[1], *baseline_trace[4:])),
            RegionView("region_C", tuple(reversed(baseline_trace))),
        )
    if scenario == "delayed_sync":
        return (
            RegionView("region_A", _delay(baseline_trace[:4], 10)),
            RegionView("region_B", _delay((baseline_trace[4], baseline_trace[5]), 20)),
            RegionView("region_C", (baseline_trace[6],)),
        )
    if scenario == "independent_recovery":
        return (
            RegionView("region_A", (baseline_trace[0], baseline_trace[2]), recovery_events=(baseline_trace[1],)),
            RegionView("region_B", (baseline_trace[3], baseline_trace[5]), recovery_events=(baseline_trace[4],)),
            RegionView("region_C", (baseline_trace[6],)),
        )
    if scenario == "duplicate_cross_region":
        return (
            RegionView("region_A", (baseline_trace[0], baseline_trace[1], baseline_trace[2], baseline_trace[2])),
            RegionView("region_B", (baseline_trace[2], baseline_trace[3], baseline_trace[4], baseline_trace[4])),
            RegionView("region_C", (baseline_trace[4], baseline_trace[5], baseline_trace[6], baseline_trace[0])),
        )
    raise ValueError(f"unknown multiregion scenario: {scenario}")


def _delay(
    events: tuple[Mapping[str, Any], ...],
    amount: int,
) -> tuple[Mapping[str, Any], ...]:
    return tuple(
        {
            **event,
            "received_order": int(event["sequence"]) + amount,
            "source": "cross_region_delayed_sync",
        }
        for event in events
    )

