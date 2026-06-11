from __future__ import annotations


def collect_runtime_events(
    *,
    errors: tuple[str, ...] = (),
    validation_failures: tuple[str, ...] = (),
    timing_violations: tuple[str, ...] = (),
    contract_mismatches: tuple[str, ...] = (),
    replay_mismatches: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "errors": errors,
        "validation_failures": validation_failures,
        "timing_violations": timing_violations,
        "contract_mismatches": contract_mismatches,
        "replay_mismatches": replay_mismatches,
        "monitoring_authority": "non_authoritative",
        "activation_allowed": False,
        "runtime_mutation_allowed": False,
        "rollback_execution_allowed": False,
    }


__all__ = ["collect_runtime_events"]
