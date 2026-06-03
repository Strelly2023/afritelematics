"""Entropy-bound execution primitives.

Failure may enter execution. Failure may not define truth.
"""

from afritech.runtime.entropy.admissibility import (
    AdmissibilityDecision,
    check_admissibility,
)
from afritech.runtime.entropy.classifier import DisturbanceType, classify
from afritech.runtime.entropy.convergence import ConvergenceResult, converge
from afritech.runtime.entropy.envelope import EntropyEnvelope
from afritech.runtime.entropy.normalizer import NormalizedEntropyEvent, normalize
from afritech.runtime.entropy.recorder import EntropyRecord, record

__all__ = [
    "AdmissibilityDecision",
    "ConvergenceResult",
    "DisturbanceType",
    "EntropyEnvelope",
    "EntropyRecord",
    "NormalizedEntropyEvent",
    "check_admissibility",
    "classify",
    "converge",
    "normalize",
    "record",
]
