# ecosystems/afriride/v0_2/execution/driver_dropout.py

from ecosystems.afriride.v0_2.execution.base import V02ScenarioExecutor


class DriverDropoutExecutor(V02ScenarioExecutor):
    """
    Deterministic executor for DRIVER_DROPOUT scenario (AfriRide v0.2).
    """

    def execute(self, scenario: dict) -> dict:
        scenario_id = scenario["id"]
        params = scenario["parameters"]

        # -------------------------------------------------
        # ✅ INITIAL STATE (DETERMINISTIC)
        # -------------------------------------------------

        initial_drivers = [
            {"id": i + 1, "available": True}
            for i in range(params["initial_driver_count"])
        ]

        before_state = {
            "drivers": list(initial_drivers),
            "dropout_count": params["dropout_count"],
        }

        # -------------------------------------------------
        # ✅ DETERMINISTIC NORMALIZATION
        # -------------------------------------------------

        ordered_drivers = sorted(initial_drivers, key=lambda d: d["id"])

        # -------------------------------------------------
        # ✅ DETERMINISTIC DROPOUT
        # -------------------------------------------------

        remaining_drivers = ordered_drivers[:-params["dropout_count"]]

        events = [
            "DriverPoolInitialized",
            "DriverPoolOrdered",
            "DriverDropoutApplied",
        ]

        # -------------------------------------------------
        # ✅ ASSIGNMENT ATTEMPTS (STRICT ORDER)
        # -------------------------------------------------

        for driver in remaining_drivers:
            events.append("AssignmentAttempted")

            if driver["available"]:
                events.append("DriverSelected")

                after_state = {
                    "selected_driver": driver["id"],
                    "remaining_drivers": [d["id"] for d in remaining_drivers],
                }

                trace = self.build_trace(
                    trace_id="driver-dropout-v0.2",
                    scenario_id=scenario_id,
                    command="ASSIGN_DRIVER",
                    guards=["DeterminismEnvelopeV02", "FailureTaxonomy"],
                    before_state=before_state,
                    after_state=after_state,
                    events=events,
                )

                return self.finalize(
                    trace=trace,
                    refusal=False,
                )

        # -------------------------------------------------
        # ✅ DETERMINISTIC EXHAUSTION / REFUSAL
        # -------------------------------------------------

        events.append("DeterministicRefusal")

        after_state = {
            "refusal_reason": "NO_DRIVER_AVAILABLE",
            "remaining_drivers": [],
        }

        trace = self.build_trace(
            trace_id="driver-dropout-v0.2",
            scenario_id=scenario_id,
            command="ASSIGN_DRIVER",
            guards=["DeterminismEnvelopeV02", "FailureTaxonomy"],
            before_state=before_state,
            after_state=after_state,
            events=events,
        )

        return self.finalize(
            trace=trace,
            refusal=True,
        )