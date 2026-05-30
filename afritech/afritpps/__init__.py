"""AfriTPPS execution pillar.

AfriTPPS defines how work gets executed across capabilities, workflows,
processes, programs, operational models, and execution metrics.
"""

from afritech.afritpps.constants import assert_afritpps_constitution
from afritech.afritpps.models import (
    AfriTPPSCapability,
    AfriTPPSProgram,
    AfriTPPSWorkflow,
    AfriTPPSWorkflowStep,
)

__all__ = [
    "AfriTPPSCapability",
    "AfriTPPSProgram",
    "AfriTPPSWorkflow",
    "AfriTPPSWorkflowStep",
    "assert_afritpps_constitution",
]
