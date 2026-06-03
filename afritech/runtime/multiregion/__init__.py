"""Multi-region convergence proof primitives."""

from afritech.runtime.multiregion.consistency_validator import (
    MultiRegionConsistency,
    validate_consistency,
)
from afritech.runtime.multiregion.convergence_engine import (
    GlobalConvergenceResult,
    converge_regions,
)
from afritech.runtime.multiregion.cross_region_sync import merge_region_traces
from afritech.runtime.multiregion.partition_simulator import partition_regions
from afritech.runtime.multiregion.region_model import RegionExecution, RegionView

__all__ = [
    "GlobalConvergenceResult",
    "MultiRegionConsistency",
    "RegionExecution",
    "RegionView",
    "converge_regions",
    "merge_region_traces",
    "partition_regions",
    "validate_consistency",
]

