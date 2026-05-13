# ecosystems/afriride/v0_2/run_multi_scenario_demo.py

"""
AFRIRIDE dropout, rejection chain, timeout), captures their decisionAFRIRIDE v0.2 — MULTI-SCENARIO CONTINUITY DEMO
traces, replays them, and verifies deterministic continuity across
multiple controlled failure modes.

CONSTITUTIONAL GUARANTEES:
- MUST NOT modify v0.1 artifacts
- MUST NOT import core/constitutional runtime directly
- MUST NOT introduce nondeterminism
- MUST NOT perform optimization or inference
- EXISTS ONLY to produce executable proof
"""

from pathlib import Path
import yaml

from ecosystems.afriride.v0_2.continuity_metrics import (
    decision_determinism_rate,
    continuity_coverage,
    deterministic_refusal_rate,
)

from ecosystems.afriride.v0_2.runtime_v02 import V02ExecutionRuntime


SCENARIO_DIR = Path("ecosystems/afriride/v0_2/scenarios")


# -------------------------------------------------
# ✅ SCENARIO LOADING (DECLARATIVE ONLY)
# -------------------------------------------------

def load_scenario(path: Path) -> dict:
    with open(path, "r") as f:
        data = yaml.safe_load(f)

    if "scenario" not in data:
        raise ValueError(f"Invalid scenario file: {path}")

    return data["scenario"]


# -------------------------------------------------
# ✅ SCENARIO EXECUTION
# -------------------------------------------------

def run_scenario(runtime: V02ExecutionRuntime, scenario: dict) -> dict:
    """
    Execute a single v0.2 scenario deterministically.
    """
    result = runtime.execute_scenario(scenario)

    return {
        "decision_hash": result["decision_hash"],
        "refusal": result.get("refusal", False),
    }


def replay_scenario(runtime: V02ExecutionRuntime, scenario: dict) -> dict:
    """
    Replay a previously executed v0.2 scenario deterministically.
    """
    replay_result = runtime.replay_scenario(scenario)

    return {
        "replay_hash": replay_result["decision_hash"],
    }


# -------------------------------------------------
# ✅ MULTI-SCENARIO PROOF RUNNER
# -------------------------------------------------

def run_multi_scenario_demo():
    print("=== AFRIRIDE v0.2 MULTI-SCENARIO CONTINUITY DEMO ===")

    runtime = V02ExecutionRuntime()

    scenario_files = [
        SCENARIO_DIR / "driver_dropout.yaml",
        SCENARIO_DIR / "rejection_chain.yaml",
        SCENARIO_DIR / "timeout.yaml",
    ]

    original_hashes = {}
    replay_hashes = {}

    total_invalid_scenarios = 0
    deterministic_refusals = 0

    for scenario_file in scenario_files:
        scenario = load_scenario(scenario_file)
        scenario_id = scenario["id"]

        print(f"\n--- Running scenario: {scenario_id} ---")

        execution_result = run_scenario(runtime, scenario)
        replay_result = replay_scenario(runtime, scenario)

        original_hashes[scenario_id] = execution_result["decision_hash"]
        replay_hashes[scenario_id] = replay_result["replay_hash"]

        ddr = decision_determinism_rate(
            execution_result["decision_hash"],
            replay_result["replay_hash"],
        )

        print(f"Decision hash : {execution_result['decision_hash']}")
        print(f"Replay hash   : {replay_result['replay_hash']}")
        print(f"DDR           : {ddr}")

        if execution_result.get("refusal", False):
            total_invalid_scenarios += 1
            deterministic_refusals += 1

        if ddr != 1.0:
            raise AssertionError(
                f"Replay mismatch detected in scenario {scenario_id}"
            )

    # -------------------------------------------------
    # ✅ CONTINUITY METRICS (v0.2)
    # -------------------------------------------------

    cc = continuity_coverage(
        total_scenarios=len(scenario_files),
        scenarios_preserving_replay=len(scenario_files),
    )

    drr = deterministic_refusal_rate(
        total_invalid_scenarios=total_invalid_scenarios,
        deterministic_refusals=deterministic_refusals,
    )

    print("\n=== AFRIRIDE v0.2 CONTINUITY METRICS ===")
    print(f"Continuity Coverage (CC): {cc}")
    print(f"Deterministic Refusal Rate (DRR): {drr}")

    print("\n✅ ALL v0.2 SCENARIOS PRESERVE CONTINUITY")
    print("✅ REPLAY VERIFIED ACROSS ALL FAILURE MODES")


# -------------------------------------------------
# ✅ ENTRYPOINT
# -------------------------------------------------

if __name__ == "__main__":
    run_multi_scenario_demo()

#This script executes all declared AfriRide v0.2 failure scenarios
