# ecosystems/afriride/v0_2/execution/rejection_chain.py

from ecosystems.afriride.v0_2.execution.base import V02ScenarioExecutor


class RejectionChainExecutor(V02ScenarioExecutor):
    """
    Deterministic executor for DRIVER_REJECTION_CHAIN scenario (AfriRide v0.2).
    """

    def execute(self, scenario: dict) -> dict:
        scenario_id = scenario["id"]
        params = scenario["parameters"]
        rejection_sequence = params["rejection_sequence"]

        # -------------------------------------------------
        # ✅ INITIAL STATE (DETERMINISTIC)
        # -------------------------------------------------

        initial_drivers = [
            {"id": i + 1, "available": True}
            for i in range(params["initial_driver_count"])
        ]

        before_state = {
            "drivers": list(initial_drivers),
            "rejection_sequence": list(rejection_sequence),
        }

        # -------------------------------------------------
        # ✅ DETERMINISTIC NORMALIZATION
        # -------------------------------------------------

        ordered_drivers = sorted(initial_drivers, key=lambda d: d["id"])

        events = [
            "DriverPoolInitialized",
            "DriverPoolOrdered",
        ]

        # -------------------------------------------------
        # ✅ ASSIGNMENT + REJECTION HANDLING (STRICT ORDER)
        # -------------------------------------------------

        for driver in ordered_drivers:
            events.append("AssignmentAttempted")

            if driver["id"] in rejection_sequence:
                events.append("DriverRejected")
                continue

            # First non-rejecting driver is selected
            events.append("DriverSelected")

            after_state = {
                "selected_driver": driver["id"],
                "rejected_drivers": list(rejection_sequence),
                "remaining_drivers": [
                    d["id"] for d in ordered_drivers if d["id"] >= driver["id"]
                ],
            }

            trace = self.build_trace(
                trace_id="rejection-chain-v0.2",
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
            "rejected_drivers": list(rejection_sequence),
            "remaining_drivers": [],
        }

        trace = self.build_trace(
            trace_id="rejection-chain-v0.2",
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