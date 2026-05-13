# ecosystems/afriride/v0_2/execution/timeout.py

from ecosystems.afriride.v0_2.execution.base import V02ScenarioExecutor


class TimeoutExecutor(V02ScenarioExecutor):
    """
    Deterministic executor for TIMEOUT_EXCEEDED scenario (AfriRide v0.2).

    Timeout is evaluated strictly using logical step counting.
    Wall-clock time, sleep, and real-time delays are constitutionally forbidden.
    """

    def execute(self, scenario: dict) -> dict:
        scenario_id = scenario["id"]
        threshold = scenario["parameters"]["timeout_threshold"]["value"]

        # -------------------------------------------------
        # ✅ INITIAL STATE (DETERMINISTIC)
        # -------------------------------------------------

        step_count = 0

        before_state = {
            "timeout_threshold": threshold,
            "initial_step_count": step_count,
        }

        events = [
            "CoordinationStarted",
        ]

        # -------------------------------------------------
        # ✅ LOGICAL STEP EXECUTION LOOP
        # -------------------------------------------------

        while True:
            step_count += 1
            events.append("CoordinationStepIncremented")

            # Timeout evaluation point (deterministic)
            if step_count > threshold:
                events.append("TimeoutThresholdEvaluated")
                events.append("DeterministicRefusal")

                after_state = {
                    "refusal_reason": "TIMEOUT_EXCEEDED",
                    "final_step_count": step_count,
                }

                trace = self.build_trace(
                    trace_id="timeout-v0.2",
                    scenario_id=scenario_id,
                    command="COORDINATION_STEP",
                    guards=["DeterminismEnvelopeV02", "FailureTaxonomy"],
                    before_state=before_state,
                    after_state=after_state,
                    events=events,
                )

                return self.finalize(
                    trace=trace,
                    refusal=True,
                )