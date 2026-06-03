"""Continuity engine.

State may be incomplete. Truth must remain reconstructable.
"""

from afritech.continuity.engine.gap_detector import ContinuityGap, detect_gaps
from afritech.continuity.engine.integrity_guard import (
    IntegrityFinding,
    guard_trace,
)
from afritech.continuity.engine.partial_replay import PartialReplayResult, partial_replay
from afritech.continuity.engine.reconstruct import (
    ReconstructionResult,
    reconstruct_trace,
)
from afritech.continuity.engine.recovery_planner import RecoveryPlan, plan_recovery

__all__ = [
    "ContinuityGap",
    "IntegrityFinding",
    "PartialReplayResult",
    "ReconstructionResult",
    "RecoveryPlan",
    "detect_gaps",
    "guard_trace",
    "partial_replay",
    "plan_recovery",
    "reconstruct_trace",
]

