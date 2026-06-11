from __future__ import annotations


def observe_runtime(
    *,
    event: str,
    state_before: str,
    expected_state: str,
    observed_state: str,
    contract: str,
    trace: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "event": event,
        "state_before": state_before,
        "expected_state": expected_state,
        "observed_state": observed_state,
        "contract": contract,
        "trace": trace or (event,),
        "observation_authority": "read_only",
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
        "rollback_execution_allowed": False,
    }


__all__ = ["observe_runtime"]
