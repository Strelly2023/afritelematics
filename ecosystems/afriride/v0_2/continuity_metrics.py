# ecosystems/afriride/v0_2/continuity_metrics.py

"""
AFRIRIDE v0.2 — CONTINUITY METRICS

This module defines the ONLY metrics permitted for AfriRide v0.2.

Purpose:
- Measure deterministic continuity across multiple scenarios
- Detect replay divergence explicitly
- Preserve v0.1 guarantees while extending coverage

This module MUST NOT:
- introduce performance metrics
- introduce optimization metrics
- introduce probabilistic analysis
- infer or smooth results

All metrics are deterministic, binary, and audit-grade.
"""


# ---------------------------------------------------------
# ✅ CORE METRIC — DECISION DETERMINISM RATE (INHERITED)
# ---------------------------------------------------------

def decision_determinism_rate(original_hash: str, replay_hash: str) -> float:
    """
    Measures whether a decision trace is replay-identical.

    Returns:
        1.0 if hashes match exactly
        0.0 otherwise
    """
    return 1.0 if original_hash == replay_hash else 0.0


# ---------------------------------------------------------
# ✅ v0.2 METRIC — CONTINUITY COVERAGE (CC)
# ---------------------------------------------------------

def continuity_coverage(total_scenarios: int, scenarios_preserving_replay: int) -> float:
    """
    Measures the proportion of declared scenarios that preserve
    deterministic replay equivalence.

    This metric answers:
    "Across all declared failure scenarios, how many remain replay-sound?"

    Returns:
        A value in [0.0, 1.0]

    Rules:
    - total_scenarios MUST be > 0
    - scenarios_preserving_replay MUST be <= total_scenarios
    """

    if total_scenarios <= 0:
        raise ValueError("total_scenarios must be greater than zero")

    if scenarios_preserving_replay < 0:
        raise ValueError("scenarios_preserving_replay cannot be negative")

    if scenarios_preserving_replay > total_scenarios:
        raise ValueError(
            "scenarios_preserving_replay cannot exceed total_scenarios"
        )

    return scenarios_preserving_replay / total_scenarios


# ---------------------------------------------------------
# ✅ v0.2 METRIC — DETERMINISTIC REFUSAL RATE (DRR)
# ---------------------------------------------------------

def deterministic_refusal_rate(
    total_invalid_scenarios: int,
    deterministic_refusals: int
) -> float:
    """
    Measures whether invalid or exhausted scenarios are rejected
    deterministically rather than failing silently or nondeterministically.

    This metric answers:
    "When refusal is required, is it always explicit and replay-safe?"

    Returns:
        A value in [0.0, 1.0]

    Rules:
    - If total_invalid_scenarios == 0, rate is defined as 1.0
    - deterministic_refusals MUST be <= total_invalid_scenarios
    """

    if total_invalid_scenarios < 0:
        raise ValueError("total_invalid_scenarios cannot be negative")

    if deterministic_refusals < 0:
        raise ValueError("deterministic_refusals cannot be negative")

    if deterministic_refusals > total_invalid_scenarios:
        raise ValueError(
            "deterministic_refusals cannot exceed total_invalid_scenarios"
        )

    if total_invalid_scenarios == 0:
        return 1.0

    return deterministic_refusals / total_invalid_scenarios


# ---------------------------------------------------------
# ✅ AGGREGATED CONTINUITY REPORT (OPTIONAL HELPER)
# ---------------------------------------------------------

def continuity_report(
    original_hashes: dict,
    replay_hashes: dict,
    total_scenarios: int,
    deterministic_refusals: int,
    total_invalid_scenarios: int
) -> dict:
    """
    Produces a deterministic continuity report across scenarios.

    This helper does NOT perform inference or aggregation beyond
    explicit metric computation.

    Returns a dictionary suitable for:
    - audit output
    - proof bundling
    - CI assertions
    """

    if original_hashes.keys() != replay_hashes.keys():
        raise ValueError(
            "Scenario keys for original and replay hashes must match exactly"
        )

    preserved = 0

    for scenario_id in original_hashes:
        if original_hashes[scenario_id] == replay_hashes[scenario_id]:
            preserved += 1

    return {
        "decision_determinism_rate_per_scenario": {
            scenario_id: decision_determinism_rate(
                original_hashes[scenario_id],
                replay_hashes[scenario_id]
            )
            for scenario_id in original_hashes
        },
        "continuity_coverage": continuity_coverage(
            total_scenarios=total_scenarios,
            scenarios_preserving_replay=preserved
        ),
        "deterministic_refusal_rate": deterministic_refusal_rate(
            total_invalid_scenarios=total_invalid_scenarios,
            deterministic_refusals=deterministic_refusals
        )
    }


# ---------------------------------------------------------
# ❌ FORBIDDEN EXTENSIONS (DOCUMENTED)
# ---------------------------------------------------------
#
# The following are intentionally NOT implemented:
#
# - latency metrics
# - throughput metrics
# - success rate metrics
# - optimization scoring
# - probabilistic confidence
# - heuristic aggregation
#
# This module exists ONLY to measure continuity, not performance.
#