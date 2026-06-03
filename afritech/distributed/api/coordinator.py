"""
afritech.distributed.api.coordinator

🔒 OPERATIVE SURFACE

This module defines the ONLY approved public interface for
distributed coordination.

All imports MUST go through this module.
"""

from __future__ import annotations


# ============================================================
# BATCH COORDINATOR (CANONICAL SOURCE)
# ============================================================

from afritech.distributed.coordinator.batch_coordinator import (
    DeterministicBatchCoordinator,
    BatchCoordinationReport,
    BatchPlan,
    build_batch_plan,
    BatchCoordinatorError,
)

# ============================================================
# CORE COORDINATOR
# ============================================================

from afritech.distributed.coordinator.coordinator import (
    CoordinationBatch,
    CoordinationResult,
    DistributedCoordinator,
    DistributedCoordinatorError,
)


# ============================================================
# OPTIONAL FACTORY (BEST PRACTICE)
# ============================================================

def build_batch_coordinator(
    *,
    coordinator: DistributedCoordinator,
    max_batch_size: int,
) -> DeterministicBatchCoordinator:
    """
    Safe factory for creating batch coordinators at API boundary.
    """
    return DeterministicBatchCoordinator(
        coordinator=coordinator,
        max_batch_size=max_batch_size,
    )


# ============================================================
# PUBLIC EXPORTS (STRICT CONTRACT)
# ============================================================

__all__ = [
    # --------------------------------------------------------
    # BATCH LAYER
    # --------------------------------------------------------
    "DeterministicBatchCoordinator",
    "BatchCoordinationReport",
    "BatchPlan",
    "build_batch_plan",
    "BatchCoordinatorError",

    # --------------------------------------------------------
    # CORE COORDINATOR
    # --------------------------------------------------------
    "CoordinationBatch",
    "CoordinationResult",
    "DistributedCoordinator",
    "DistributedCoordinatorError",

    # --------------------------------------------------------
    # FACTORIES
    # --------------------------------------------------------
    "build_batch_coordinator",
]
