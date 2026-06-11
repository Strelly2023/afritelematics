from __future__ import annotations


def evaluate_contracts(observation: dict[str, object]) -> dict[str, object]:
    expected = observation.get("expected_state")
    observed = observation.get("observed_state")
    compliant = expected == observed
    return {
        "contract": observation.get("contract"),
        "event": observation.get("event"),
        "compliant": compliant,
        "expected_behavior": expected,
        "observed_behavior": observed,
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
    }


__all__ = ["evaluate_contracts"]
