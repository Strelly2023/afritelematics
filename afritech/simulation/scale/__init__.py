"""
afritech.simulation.scale

Deterministic scale simulation surfaces.

Public API for:
- multi-node simulation
- deterministic load generation
- failure injection
"""

# ============================================================
# CLUSTER SIMULATOR
# ============================================================

from afritech.simulation.scale.cluster_simulator import (
    DeterministicClusterSimulator,
)

# ✅ public alias (stable API surface)
ClusterSimulator = DeterministicClusterSimulator


# ============================================================
# LOAD GENERATOR
# ============================================================

from afritech.simulation.scale.load_generator import (
    generate_events,
    generate_profile,
    generate_partition_skewed_events,
    generate_burst_events,
    LoadProfile,
)


# ============================================================
# FAILURE INJECTOR
# ============================================================

from afritech.simulation.scale.failure_injector import (
    maybe_inject_worker_failure,
    safe_execute_with_injection,
    apply_failure_strategy,
    FailurePolicy,
    SimulatedWorkerFailure,
)


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # --- cluster ---
    "ClusterSimulator",
    "DeterministicClusterSimulator",

    # --- load ---
    "generate_events",
    "generate_profile",
    "generate_partition_skewed_events",
    "generate_burst_events",
    "LoadProfile",

    # --- failure ---
    "maybe_inject_worker_failure",
    "safe_execute_with_injection",
    "apply_failure_strategy",
    "FailurePolicy",
    "SimulatedWorkerFailure",
]